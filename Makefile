run:
	./main.py

git-push-tg:
	git subtree push --prefix website/Learnings_from_AeN_template_generator/ https://github.com/SIOS-Svalbard/Learnings_from_AeN_template_generator.git main

git-pull-tg:
	git subtree pull --prefix website/Learnings_from_AeN_template_generator/ --squash https://github.com/SIOS-Svalbard/Learnings_from_AeN_template_generator.git main

git-push-lp:
	git subtree push --prefix website/Learnings_from_AeN_label_printing/ https://github.com/SIOS-Svalbard/Learnings_from_AeN_label_printing.git main

git-pull-lp:
	git subtree pull --prefix website/Learnings_from_AeN_label_printing/ --squash https://github.com/SIOS-Svalbard/Learnings_from_AeN_label_printing.git main
