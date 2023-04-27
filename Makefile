run:
	./main.py

git-push-tg:
	git subtree push --prefix website/templategenerator/ https://github.com/SIOS-Svalbard/Learnings_from_AeN_template_generator.git main

git-pull-tg:
	git subtree pull --prefix website/templategenerator/ --squash https://github.com/SIOS-Svalbard/Learnings_from_AeN_template_generator.git main
