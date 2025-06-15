- Support loading `.env` file for ENV based secrets
- May be an option 2 specify schema path?
- Support to add schemas without interaction.
- Updating schema or schema migration. Cases like default value change / path change / deletion etc.
- value from multiple options (eg: value should be one of [a,b,c])
- Should we migrate to existing helm values schema for this plugin?
- Nice to have: completion based on resources in json files.
- Nice to have: completion for plugin
- Nice to have: publish as pip installable bin

bugs
- While using `helm-values-manager values init` or `helm-values-manager values set` what is the difference between n/skip both seems to do same functionality

- `helm-values-manager values init -f` is only supposed to skip default value's prompt and ask others. But looks like it add the default values in to the values json file while not prompting others. Either -f should skip the defaults all together and ask about others. Or we should add new option to skip defaults. What do you think?