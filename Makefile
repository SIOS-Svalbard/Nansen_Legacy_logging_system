run:
	./main.py

git-push-tg:
	git subtree push --prefix website/template-generator/ template-generator main

git-pull-tg:
	git subtree pull --prefix website/template-generator/ --squash template-generator main
