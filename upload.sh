pandoc --from=markdown --to=rst --output=README.txt README.md
rm -rf dist build
python setup.py sdist bdist_wheel
twine upload -r pypi dist/*
