git push origin master
git push github master
bash scripts/clean.sh
bash scripts/build.sh
twine upload dist/* --verbose # setup your pypi username and password in ~/.pypirc