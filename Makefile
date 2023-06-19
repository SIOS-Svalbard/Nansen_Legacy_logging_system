run:
	./main.py

git-push-tg:
	git subtree push --prefix website/Learnings_from_AeN_template_generator/ https://github.com/SIOS-Svalbard/Learnings_from_AeN_template_generator.git main

git-pull-tg:
	git subtree pull --prefix website/Learnings_from_AeN_template_generator/ --squash https://github.com/SIOS-Svalbard/Learnings_from_AeN_template_generator.git main
