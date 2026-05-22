# fs-features pipeline.
#
# Targets:
#   make           -- run the whole pipeline (enrich, analyze, plot, html)
#   make enrich    -- update merged_date/version/Fixes from kernel tree
#   make analyze   -- compute metrics, emit CSV/JSON/Markdown
#   make plots     -- render PNG figures
#   make report    -- build docs/index.html
#   make clean     -- remove generated outputs
#   make whitespace-fix -- normalize trailing whitespace and newlines
#   make whitespace-check -- check without modifying

PYTHON ?= python3
KERNEL_TREE ?= $(HOME)/linux
SCRIPTS := scripts
DATA := data
DOCS := docs
REPORTS := reports

FEATURE_JSONS := $(wildcard $(DATA)/features_*.json)

.PHONY: all enrich analyze plots report clean whitespace-fix whitespace-check

all: enrich analyze plots report

enrich:
	$(PYTHON) $(SCRIPTS)/enrich.py --tree $(KERNEL_TREE)

analyze: $(DATA)/analysis.json
$(DATA)/analysis.json: $(FEATURE_JSONS) $(SCRIPTS)/analyze.py
	$(PYTHON) $(SCRIPTS)/analyze.py

plots: $(DOCS)/images/timeline.png
$(DOCS)/images/timeline.png: $(FEATURE_JSONS) $(SCRIPTS)/plot.py
	$(PYTHON) $(SCRIPTS)/plot.py

report: $(DOCS)/index.html $(DOCS)/findings.html
$(DOCS)/index.html: $(FEATURE_JSONS) $(DATA)/analysis.json $(SCRIPTS)/build_html.py
	$(PYTHON) $(SCRIPTS)/build_html.py
$(DOCS)/findings.html: $(REPORTS)/findings.md $(SCRIPTS)/render_findings.py
	$(PYTHON) $(SCRIPTS)/render_findings.py

clean:
	rm -f $(DATA)/features_all.csv $(DATA)/analysis.json
	rm -f $(REPORTS)/analysis.md
	rm -f $(DOCS)/index.html $(DOCS)/findings.html
	rm -f $(DOCS)/*.csv $(DOCS)/*.json $(DOCS)/*.md
	rm -rf $(DOCS)/images

whitespace-fix:
	$(PYTHON) $(SCRIPTS)/fix_whitespace_issues.py .

whitespace-check:
	$(PYTHON) $(SCRIPTS)/fix_whitespace_issues.py --check .
