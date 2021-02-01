# Simple Service Registration

## Description

This skill registers and unregisters an agent and service on the sOEF.

This skill is used in the "Guide on Writing a Skill" section in the documentation. On start, it registers an agent and its service on the sOEF, and on termination it unregisters the agent and its service from sOEF.

## Behaviours

* `service`: registers and unregisters a service on the sOEF 

## Handlers

* `oef_search`: handles `oef_search` messages if interactions with the sOEF is erratic

## Links

* <a href="https://docs.fetch.ai/aea/skill-guide/" target="_blank">Guide on Building a Skill</a>
