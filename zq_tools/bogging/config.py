# Copyright 2001-2019 by Vinay Sajip. All Rights Reserved.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation, and that the name of Vinay Sajip
# not be used in advertising or publicity pertaining to distribution
# of the software without specific, written prior permission.
# VINAY SAJIP DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
# ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL
# VINAY SAJIP BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR
# ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER
# IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
Configuration functions for the bogging package for Python. The core package
is based on PEP 282 and comments thereto in comp.lang.python, and influenced
by Apache's bog4j system.

Copyright (C) 2001-2019 Vinay Sajip. All Rights Reserved.

To use, simply 'import bogging' and bog away!
"""

import errno
import io
import bogging
import bogging.handlers
import re
import struct
import sys
import threading
import traceback

from socketserver import ThreadingTCPServer, StreamRequestHandler


DEFAULT_LOGGING_CONFIG_PORT = 9030

RESET_ERROR = errno.ECONNRESET

#
#   The following code implements a socket listener for on-the-fly
#   reconfiguration of bogging.
#
#   _listener holds the server object doing the listening
_listener = None

def fileConfig(fname, defaults=None, disable_existing_boggers=True):
    """
    Read the bogging configuration from a ConfigParser-format file.

    This can be called several times from an application, allowing an end user
    the ability to select from various pre-canned configurations (if the
    developer provides a mechanism to present the choices and load the chosen
    configuration).
    """
    import configparser

    if isinstance(fname, configparser.RawConfigParser):
        cp = fname
    else:
        cp = configparser.ConfigParser(defaults)
        if hasattr(fname, 'readline'):
            cp.read_file(fname)
        else:
            cp.read(fname)

    formatters = _create_formatters(cp)

    # critical section
    bogging._acquireLock()
    try:
        _clearExistingHandlers()

        # Handlers add themselves to bogging._handlers
        handlers = _install_handlers(cp, formatters)
        _install_boggers(cp, handlers, disable_existing_boggers)
    finally:
        bogging._releaseLock()


def _resolve(name):
    """Resolve a dotted name to a global object."""
    name = name.split('.')
    used = name.pop(0)
    found = __import__(used)
    for n in name:
        used = used + '.' + n
        try:
            found = getattr(found, n)
        except AttributeError:
            __import__(used)
            found = getattr(found, n)
    return found

def _strip_spaces(alist):
    return map(str.strip, alist)

def _create_formatters(cp):
    """Create and return formatters"""
    flist = cp["formatters"]["keys"]
    if not len(flist):
        return {}
    flist = flist.split(",")
    flist = _strip_spaces(flist)
    formatters = {}
    for form in flist:
        sectname = "formatter_%s" % form
        fs = cp.get(sectname, "format", raw=True, fallback=None)
        dfs = cp.get(sectname, "datefmt", raw=True, fallback=None)
        stl = cp.get(sectname, "style", raw=True, fallback='%')
        c = bogging.Formatter
        class_name = cp[sectname].get("class")
        if class_name:
            c = _resolve(class_name)
        f = c(fs, dfs, stl)
        formatters[form] = f
    return formatters


def _install_handlers(cp, formatters):
    """Install and return handlers"""
    hlist = cp["handlers"]["keys"]
    if not len(hlist):
        return {}
    hlist = hlist.split(",")
    hlist = _strip_spaces(hlist)
    handlers = {}
    fixups = [] #for inter-handler references
    for hand in hlist:
        section = cp["handler_%s" % hand]
        klass = section["class"]
        fmt = section.get("formatter", "")
        try:
            klass = eval(klass, vars(bogging))
        except (AttributeError, NameError):
            klass = _resolve(klass)
        args = section.get("args", '()')
        args = eval(args, vars(bogging))
        kwargs = section.get("kwargs", '{}')
        kwargs = eval(kwargs, vars(bogging))
        h = klass(*args, **kwargs)
        h.name = hand
        if "level" in section:
            level = section["level"]
            h.setLevel(level)
        if len(fmt):
            h.setFormatter(formatters[fmt])
        if issubclass(klass, bogging.handlers.MemoryHandler):
            target = section.get("target", "")
            if len(target): #the target handler may not be loaded yet, so keep for later...
                fixups.append((h, target))
        handlers[hand] = h
    #now all handlers are loaded, fixup inter-handler references...
    for h, t in fixups:
        h.setTarget(handlers[t])
    return handlers

def _handle_existing_boggers(existing, child_boggers, disable_existing):
    """
    When (re)configuring bogging, handle boggers which were in the previous
    configuration but are not in the new configuration. There's no point
    deleting them as other threads may continue to hold references to them;
    and by disabling them, you stop them doing any bogging.

    However, don't disable children of named boggers, as that's probably not
    what was intended by the user. Also, allow existing boggers to NOT be
    disabled if disable_existing is false.
    """
    root = bogging.root
    for bog in existing:
        bogger = root.manager.boggerDict[bog]
        if bog in child_boggers:
            if not isinstance(bogger, bogging.PlaceHolder):
                bogger.setLevel(bogging.NOTSET)
                bogger.handlers = []
                bogger.propagate = True
        else:
            bogger.disabled = disable_existing

def _install_boggers(cp, handlers, disable_existing):
    """Create and install boggers"""

    # configure the root first
    llist = cp["boggers"]["keys"]
    llist = llist.split(",")
    llist = list(_strip_spaces(llist))
    llist.remove("root")
    section = cp["bogger_root"]
    root = bogging.root
    bog = root
    if "level" in section:
        level = section["level"]
        bog.setLevel(level)
    for h in root.handlers[:]:
        root.removeHandler(h)
    hlist = section["handlers"]
    if len(hlist):
        hlist = hlist.split(",")
        hlist = _strip_spaces(hlist)
        for hand in hlist:
            bog.addHandler(handlers[hand])

    #and now the others...
    #we don't want to lose the existing boggers,
    #since other threads may have pointers to them.
    #existing is set to contain all existing boggers,
    #and as we go through the new configuration we
    #remove any which are configured. At the end,
    #what's left in existing is the set of boggers
    #which were in the previous configuration but
    #which are not in the new configuration.
    existing = list(root.manager.boggerDict.keys())
    #The list needs to be sorted so that we can
    #avoid disabling child boggers of explicitly
    #named boggers. With a sorted list it is easier
    #to find the child boggers.
    existing.sort()
    #We'll keep the list of existing boggers
    #which are children of named boggers here...
    child_boggers = []
    #now set up the new ones...
    for bog in llist:
        section = cp["bogger_%s" % bog]
        qn = section["qualname"]
        propagate = section.getint("propagate", fallback=1)
        bogger = bogging.getBogger(qn)
        if qn in existing:
            i = existing.index(qn) + 1 # start with the entry after qn
            prefixed = qn + "."
            pflen = len(prefixed)
            num_existing = len(existing)
            while i < num_existing:
                if existing[i][:pflen] == prefixed:
                    child_boggers.append(existing[i])
                i += 1
            existing.remove(qn)
        if "level" in section:
            level = section["level"]
            bogger.setLevel(level)
        for h in bogger.handlers[:]:
            bogger.removeHandler(h)
        bogger.propagate = propagate
        bogger.disabled = 0
        hlist = section["handlers"]
        if len(hlist):
            hlist = hlist.split(",")
            hlist = _strip_spaces(hlist)
            for hand in hlist:
                bogger.addHandler(handlers[hand])

    #Disable any old boggers. There's no point deleting
    #them as other threads may continue to hold references
    #and by disabling them, you stop them doing any bogging.
    #However, don't disable children of named boggers, as that's
    #probably not what was intended by the user.
    #for bog in existing:
    #    bogger = root.manager.boggerDict[bog]
    #    if bog in child_boggers:
    #        bogger.level = bogging.NOTSET
    #        bogger.handlers = []
    #        bogger.propagate = 1
    #    elif disable_existing_boggers:
    #        bogger.disabled = 1
    _handle_existing_boggers(existing, child_boggers, disable_existing)


def _clearExistingHandlers():
    """Clear and close existing handlers"""
    bogging._handlers.clear()
    bogging.shutdown(bogging._handlerList[:])
    del bogging._handlerList[:]


IDENTIFIER = re.compile('^[a-z_][a-z0-9_]*$', re.I)


def valid_ident(s):
    m = IDENTIFIER.match(s)
    if not m:
        raise ValueError('Not a valid Python identifier: %r' % s)
    return True


class ConvertingMixin(object):
    """For ConvertingXXX's, this mixin class provides common functions"""

    def convert_with_key(self, key, value, replace=True):
        result = self.configurator.convert(value)
        #If the converted value is different, save for next time
        if value is not result:
            if replace:
                self[key] = result
            if type(result) in (ConvertingDict, ConvertingList,
                               ConvertingTuple):
                result.parent = self
                result.key = key
        return result

    def convert(self, value):
        result = self.configurator.convert(value)
        if value is not result:
            if type(result) in (ConvertingDict, ConvertingList,
                               ConvertingTuple):
                result.parent = self
        return result


# The ConvertingXXX classes are wrappers around standard Python containers,
# and they serve to convert any suitable values in the container. The
# conversion converts base dicts, lists and tuples to their wrapped
# equivalents, whereas strings which match a conversion format are converted
# appropriately.
#
# Each wrapper should have a configurator attribute holding the actual
# configurator to use for conversion.

class ConvertingDict(dict, ConvertingMixin):
    """A converting dictionary wrapper."""

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        return self.convert_with_key(key, value)

    def get(self, key, default=None):
        value = dict.get(self, key, default)
        return self.convert_with_key(key, value)

    def pop(self, key, default=None):
        value = dict.pop(self, key, default)
        return self.convert_with_key(key, value, replace=False)

class ConvertingList(list, ConvertingMixin):
    """A converting list wrapper."""
    def __getitem__(self, key):
        value = list.__getitem__(self, key)
        return self.convert_with_key(key, value)

    def pop(self, idx=-1):
        value = list.pop(self, idx)
        return self.convert(value)

class ConvertingTuple(tuple, ConvertingMixin):
    """A converting tuple wrapper."""
    def __getitem__(self, key):
        value = tuple.__getitem__(self, key)
        # Can't replace a tuple entry.
        return self.convert_with_key(key, value, replace=False)

class BaseConfigurator(object):
    """
    The configurator base class which defines some useful defaults.
    """

    CONVERT_PATTERN = re.compile(r'^(?P<prefix>[a-z]+)://(?P<suffix>.*)$')

    WORD_PATTERN = re.compile(r'^\s*(\w+)\s*')
    DOT_PATTERN = re.compile(r'^\.\s*(\w+)\s*')
    INDEX_PATTERN = re.compile(r'^\[\s*(\w+)\s*\]\s*')
    DIGIT_PATTERN = re.compile(r'^\d+$')

    value_converters = {
        'ext' : 'ext_convert',
        'cfg' : 'cfg_convert',
    }

    # We might want to use a different one, e.g. importlib
    importer = staticmethod(__import__)

    def __init__(self, config):
        self.config = ConvertingDict(config)
        self.config.configurator = self

    def resolve(self, s):
        """
        Resolve strings to objects using standard import and attribute
        syntax.
        """
        name = s.split('.')
        used = name.pop(0)
        try:
            found = self.importer(used)
            for frag in name:
                used += '.' + frag
                try:
                    found = getattr(found, frag)
                except AttributeError:
                    self.importer(used)
                    found = getattr(found, frag)
            return found
        except ImportError:
            e, tb = sys.exc_info()[1:]
            v = ValueError('Cannot resolve %r: %s' % (s, e))
            v.__cause__, v.__traceback__ = e, tb
            raise v

    def ext_convert(self, value):
        """Default converter for the ext:// protocol."""
        return self.resolve(value)

    def cfg_convert(self, value):
        """Default converter for the cfg:// protocol."""
        rest = value
        m = self.WORD_PATTERN.match(rest)
        if m is None:
            raise ValueError("Unable to convert %r" % value)
        else:
            rest = rest[m.end():]
            d = self.config[m.groups()[0]]
            #print d, rest
            while rest:
                m = self.DOT_PATTERN.match(rest)
                if m:
                    d = d[m.groups()[0]]
                else:
                    m = self.INDEX_PATTERN.match(rest)
                    if m:
                        idx = m.groups()[0]
                        if not self.DIGIT_PATTERN.match(idx):
                            d = d[idx]
                        else:
                            try:
                                n = int(idx) # try as number first (most likely)
                                d = d[n]
                            except TypeError:
                                d = d[idx]
                if m:
                    rest = rest[m.end():]
                else:
                    raise ValueError('Unable to convert '
                                     '%r at %r' % (value, rest))
        #rest should be empty
        return d

    def convert(self, value):
        """
        Convert values to an appropriate type. dicts, lists and tuples are
        replaced by their converting alternatives. Strings are checked to
        see if they have a conversion format and are converted if they do.
        """
        if not isinstance(value, ConvertingDict) and isinstance(value, dict):
            value = ConvertingDict(value)
            value.configurator = self
        elif not isinstance(value, ConvertingList) and isinstance(value, list):
            value = ConvertingList(value)
            value.configurator = self
        elif not isinstance(value, ConvertingTuple) and\
                 isinstance(value, tuple) and not hasattr(value, '_fields'):
            value = ConvertingTuple(value)
            value.configurator = self
        elif isinstance(value, str): # str for py3k
            m = self.CONVERT_PATTERN.match(value)
            if m:
                d = m.groupdict()
                prefix = d['prefix']
                converter = self.value_converters.get(prefix, None)
                if converter:
                    suffix = d['suffix']
                    converter = getattr(self, converter)
                    value = converter(suffix)
        return value

    def configure_custom(self, config):
        """Configure an object with a user-supplied factory."""
        c = config.pop('()')
        if not callable(c):
            c = self.resolve(c)
        props = config.pop('.', None)
        # Check for valid identifiers
        kwargs = {k: config[k] for k in config if valid_ident(k)}
        result = c(**kwargs)
        if props:
            for name, value in props.items():
                setattr(result, name, value)
        return result

    def as_tuple(self, value):
        """Utility function which converts lists to tuples."""
        if isinstance(value, list):
            value = tuple(value)
        return value

class DictConfigurator(BaseConfigurator):
    """
    Configure bogging using a dictionary-like object to describe the
    configuration.
    """

    def configure(self):
        """Do the configuration."""

        config = self.config
        if 'version' not in config:
            raise ValueError("dictionary doesn't specify a version")
        if config['version'] != 1:
            raise ValueError("Unsupported version: %s" % config['version'])
        incremental = config.pop('incremental', False)
        EMPTY_DICT = {}
        bogging._acquireLock()
        try:
            if incremental:
                handlers = config.get('handlers', EMPTY_DICT)
                for name in handlers:
                    if name not in bogging._handlers:
                        raise ValueError('No handler found with '
                                         'name %r'  % name)
                    else:
                        try:
                            handler = bogging._handlers[name]
                            handler_config = handlers[name]
                            level = handler_config.get('level', None)
                            if level:
                                handler.setLevel(bogging._checkLevel(level))
                        except Exception as e:
                            raise ValueError('Unable to configure handler '
                                             '%r' % name) from e
                boggers = config.get('boggers', EMPTY_DICT)
                for name in boggers:
                    try:
                        self.configure_bogger(name, boggers[name], True)
                    except Exception as e:
                        raise ValueError('Unable to configure bogger '
                                         '%r' % name) from e
                root = config.get('root', None)
                if root:
                    try:
                        self.configure_root(root, True)
                    except Exception as e:
                        raise ValueError('Unable to configure root '
                                         'bogger') from e
            else:
                disable_existing = config.pop('disable_existing_boggers', True)

                _clearExistingHandlers()

                # Do formatters first - they don't refer to anything else
                formatters = config.get('formatters', EMPTY_DICT)
                for name in formatters:
                    try:
                        formatters[name] = self.configure_formatter(
                                                            formatters[name])
                    except Exception as e:
                        raise ValueError('Unable to configure '
                                         'formatter %r' % name) from e
                # Next, do filters - they don't refer to anything else, either
                filters = config.get('filters', EMPTY_DICT)
                for name in filters:
                    try:
                        filters[name] = self.configure_filter(filters[name])
                    except Exception as e:
                        raise ValueError('Unable to configure '
                                         'filter %r' % name) from e

                # Next, do handlers - they refer to formatters and filters
                # As handlers can refer to other handlers, sort the keys
                # to allow a deterministic order of configuration
                handlers = config.get('handlers', EMPTY_DICT)
                deferred = []
                for name in sorted(handlers):
                    try:
                        handler = self.configure_handler(handlers[name])
                        handler.name = name
                        handlers[name] = handler
                    except Exception as e:
                        if 'target not configured yet' in str(e.__cause__):
                            deferred.append(name)
                        else:
                            raise ValueError('Unable to configure handler '
                                             '%r' % name) from e

                # Now do any that were deferred
                for name in deferred:
                    try:
                        handler = self.configure_handler(handlers[name])
                        handler.name = name
                        handlers[name] = handler
                    except Exception as e:
                        raise ValueError('Unable to configure handler '
                                         '%r' % name) from e

                # Next, do boggers - they refer to handlers and filters

                #we don't want to lose the existing boggers,
                #since other threads may have pointers to them.
                #existing is set to contain all existing boggers,
                #and as we go through the new configuration we
                #remove any which are configured. At the end,
                #what's left in existing is the set of boggers
                #which were in the previous configuration but
                #which are not in the new configuration.
                root = bogging.root
                existing = list(root.manager.boggerDict.keys())
                #The list needs to be sorted so that we can
                #avoid disabling child boggers of explicitly
                #named boggers. With a sorted list it is easier
                #to find the child boggers.
                existing.sort()
                #We'll keep the list of existing boggers
                #which are children of named boggers here...
                child_boggers = []
                #now set up the new ones...
                boggers = config.get('boggers', EMPTY_DICT)
                for name in boggers:
                    if name in existing:
                        i = existing.index(name) + 1 # look after name
                        prefixed = name + "."
                        pflen = len(prefixed)
                        num_existing = len(existing)
                        while i < num_existing:
                            if existing[i][:pflen] == prefixed:
                                child_boggers.append(existing[i])
                            i += 1
                        existing.remove(name)
                    try:
                        self.configure_bogger(name, boggers[name])
                    except Exception as e:
                        raise ValueError('Unable to configure bogger '
                                         '%r' % name) from e

                #Disable any old boggers. There's no point deleting
                #them as other threads may continue to hold references
                #and by disabling them, you stop them doing any bogging.
                #However, don't disable children of named boggers, as that's
                #probably not what was intended by the user.
                #for bog in existing:
                #    bogger = root.manager.boggerDict[bog]
                #    if bog in child_boggers:
                #        bogger.level = bogging.NOTSET
                #        bogger.handlers = []
                #        bogger.propagate = True
                #    elif disable_existing:
                #        bogger.disabled = True
                _handle_existing_boggers(existing, child_boggers,
                                         disable_existing)

                # And finally, do the root bogger
                root = config.get('root', None)
                if root:
                    try:
                        self.configure_root(root)
                    except Exception as e:
                        raise ValueError('Unable to configure root '
                                         'bogger') from e
        finally:
            bogging._releaseLock()

    def configure_formatter(self, config):
        """Configure a formatter from a dictionary."""
        if '()' in config:
            factory = config['()'] # for use in exception handler
            try:
                result = self.configure_custom(config)
            except TypeError as te:
                if "'format'" not in str(te):
                    raise
                #Name of parameter changed from fmt to format.
                #Retry with old name.
                #This is so that code can be used with older Python versions
                #(e.g. by Django)
                config['fmt'] = config.pop('format')
                config['()'] = factory
                result = self.configure_custom(config)
        else:
            fmt = config.get('format', None)
            dfmt = config.get('datefmt', None)
            style = config.get('style', '%')
            cname = config.get('class', None)

            if not cname:
                c = bogging.Formatter
            else:
                c = _resolve(cname)

            # A TypeError would be raised if "validate" key is passed in with a formatter callable
            # that does not accept "validate" as a parameter
            if 'validate' in config:  # if user hasn't mentioned it, the default will be fine
                result = c(fmt, dfmt, style, config['validate'])
            else:
                result = c(fmt, dfmt, style)

        return result

    def configure_filter(self, config):
        """Configure a filter from a dictionary."""
        if '()' in config:
            result = self.configure_custom(config)
        else:
            name = config.get('name', '')
            result = bogging.Filter(name)
        return result

    def add_filters(self, filterer, filters):
        """Add filters to a filterer from a list of names."""
        for f in filters:
            try:
                filterer.addFilter(self.config['filters'][f])
            except Exception as e:
                raise ValueError('Unable to add filter %r' % f) from e

    def configure_handler(self, config):
        """Configure a handler from a dictionary."""
        config_copy = dict(config)  # for restoring in case of error
        formatter = config.pop('formatter', None)
        if formatter:
            try:
                formatter = self.config['formatters'][formatter]
            except Exception as e:
                raise ValueError('Unable to set formatter '
                                 '%r' % formatter) from e
        level = config.pop('level', None)
        filters = config.pop('filters', None)
        if '()' in config:
            c = config.pop('()')
            if not callable(c):
                c = self.resolve(c)
            factory = c
        else:
            cname = config.pop('class')
            klass = self.resolve(cname)
            #Special case for handler which refers to another handler
            if issubclass(klass, bogging.handlers.MemoryHandler) and\
                'target' in config:
                try:
                    th = self.config['handlers'][config['target']]
                    if not isinstance(th, bogging.Handler):
                        config.update(config_copy)  # restore for deferred cfg
                        raise TypeError('target not configured yet')
                    config['target'] = th
                except Exception as e:
                    raise ValueError('Unable to set target handler '
                                     '%r' % config['target']) from e
            elif issubclass(klass, bogging.handlers.SMTPHandler) and\
                'mailhost' in config:
                config['mailhost'] = self.as_tuple(config['mailhost'])
            elif issubclass(klass, bogging.handlers.SysBogHandler) and\
                'address' in config:
                config['address'] = self.as_tuple(config['address'])
            factory = klass
        props = config.pop('.', None)
        kwargs = {k: config[k] for k in config if valid_ident(k)}
        try:
            result = factory(**kwargs)
        except TypeError as te:
            if "'stream'" not in str(te):
                raise
            #The argument name changed from strm to stream
            #Retry with old name.
            #This is so that code can be used with older Python versions
            #(e.g. by Django)
            kwargs['strm'] = kwargs.pop('stream')
            result = factory(**kwargs)
        if formatter:
            result.setFormatter(formatter)
        if level is not None:
            result.setLevel(bogging._checkLevel(level))
        if filters:
            self.add_filters(result, filters)
        if props:
            for name, value in props.items():
                setattr(result, name, value)
        return result

    def add_handlers(self, bogger, handlers):
        """Add handlers to a bogger from a list of names."""
        for h in handlers:
            try:
                bogger.addHandler(self.config['handlers'][h])
            except Exception as e:
                raise ValueError('Unable to add handler %r' % h) from e

    def common_bogger_config(self, bogger, config, incremental=False):
        """
        Perform configuration which is common to root and non-root boggers.
        """
        level = config.get('level', None)
        if level is not None:
            bogger.setLevel(bogging._checkLevel(level))
        if not incremental:
            #Remove any existing handlers
            for h in bogger.handlers[:]:
                bogger.removeHandler(h)
            handlers = config.get('handlers', None)
            if handlers:
                self.add_handlers(bogger, handlers)
            filters = config.get('filters', None)
            if filters:
                self.add_filters(bogger, filters)

    def configure_bogger(self, name, config, incremental=False):
        """Configure a non-root bogger from a dictionary."""
        bogger = bogging.getBogger(name)
        self.common_bogger_config(bogger, config, incremental)
        propagate = config.get('propagate', None)
        if propagate is not None:
            bogger.propagate = propagate

    def configure_root(self, config, incremental=False):
        """Configure a root bogger from a dictionary."""
        root = bogging.getBogger()
        self.common_bogger_config(root, config, incremental)

dictConfigClass = DictConfigurator

def dictConfig(config):
    """Configure bogging using a dictionary."""
    dictConfigClass(config).configure()


def listen(port=DEFAULT_LOGGING_CONFIG_PORT, verify=None):
    """
    Start up a socket server on the specified port, and listen for new
    configurations.

    These will be sent as a file suitable for processing by fileConfig().
    Returns a Thread object on which you can call start() to start the server,
    and which you can join() when appropriate. To stop the server, call
    stopListening().

    Use the ``verify`` argument to verify any bytes received across the wire
    from a client. If specified, it should be a callable which receives a
    single argument - the bytes of configuration data received across the
    network - and it should return either ``None``, to indicate that the
    passed in bytes could not be verified and should be discarded, or a
    byte string which is then passed to the configuration machinery as
    normal. Note that you can return transformed bytes, e.g. by decrypting
    the bytes passed in.
    """

    class ConfigStreamHandler(StreamRequestHandler):
        """
        Handler for a bogging configuration request.

        It expects a completely new bogging configuration and uses fileConfig
        to install it.
        """
        def handle(self):
            """
            Handle a request.

            Each request is expected to be a 4-byte length, packed using
            struct.pack(">L", n), followed by the config file.
            Uses fileConfig() to do the grunt work.
            """
            try:
                conn = self.connection
                chunk = conn.recv(4)
                if len(chunk) == 4:
                    slen = struct.unpack(">L", chunk)[0]
                    chunk = self.connection.recv(slen)
                    while len(chunk) < slen:
                        chunk = chunk + conn.recv(slen - len(chunk))
                    if self.server.verify is not None:
                        chunk = self.server.verify(chunk)
                    if chunk is not None:   # verified, can process
                        chunk = chunk.decode("utf-8")
                        try:
                            import json
                            d =json.loads(chunk)
                            assert isinstance(d, dict)
                            dictConfig(d)
                        except Exception:
                            #Apply new configuration.

                            file = io.StringIO(chunk)
                            try:
                                fileConfig(file)
                            except Exception:
                                traceback.print_exc()
                    if self.server.ready:
                        self.server.ready.set()
            except OSError as e:
                if e.errno != RESET_ERROR:
                    raise

    class ConfigSocketReceiver(ThreadingTCPServer):
        """
        A simple TCP socket-based bogging config receiver.
        """

        allow_reuse_address = 1

        def __init__(self, host='localhost', port=DEFAULT_LOGGING_CONFIG_PORT,
                     handler=None, ready=None, verify=None):
            ThreadingTCPServer.__init__(self, (host, port), handler)
            bogging._acquireLock()
            self.abort = 0
            bogging._releaseLock()
            self.timeout = 1
            self.ready = ready
            self.verify = verify

        def serve_until_stopped(self):
            import select
            abort = 0
            while not abort:
                rd, wr, ex = select.select([self.socket.fileno()],
                                           [], [],
                                           self.timeout)
                if rd:
                    self.handle_request()
                bogging._acquireLock()
                abort = self.abort
                bogging._releaseLock()
            self.server_close()

    class Server(threading.Thread):

        def __init__(self, rcvr, hdlr, port, verify):
            super(Server, self).__init__()
            self.rcvr = rcvr
            self.hdlr = hdlr
            self.port = port
            self.verify = verify
            self.ready = threading.Event()

        def run(self):
            server = self.rcvr(port=self.port, handler=self.hdlr,
                               ready=self.ready,
                               verify=self.verify)
            if self.port == 0:
                self.port = server.server_address[1]
            self.ready.set()
            global _listener
            bogging._acquireLock()
            _listener = server
            bogging._releaseLock()
            server.serve_until_stopped()

    return Server(ConfigSocketReceiver, ConfigStreamHandler, port, verify)

def stopListening():
    """
    Stop the listening server which was created with a call to listen().
    """
    global _listener
    bogging._acquireLock()
    try:
        if _listener:
            _listener.abort = 1
            _listener = None
    finally:
        bogging._releaseLock()
