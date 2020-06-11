#!/bin/bash
cd .. && pytest --cov-branch --cov-report=html:test_coverage/ --cov=./ test/
