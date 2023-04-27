run:
	./main.py

git-push-tg:
	git subtree push --prefix website/templategenerator/ templategenerator main

git-pull-tg:
	git subtree pull --prefix website/templategenerator/ --squash templategenerator main
