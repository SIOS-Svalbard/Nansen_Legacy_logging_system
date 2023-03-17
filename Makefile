run:
	./main.py

git-push-tg:
	git subtree push --prefix website/templategenerator/ template-generator main

git-pull-tg:
	git subtree pull --prefix website/templategenerator/ --squash template-generator main
