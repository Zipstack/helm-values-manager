I want to build a helm plugin that helps manage the helm value configurations for different deployments with upgrade support. We will call it helm-values-manager.

## Features
- Will be a helm plugin that generates values yaml files for different deployments of same charts (like in dev, test, prod etc)
- Should be usable with existing CD systems like argo
- Manage values config which can contain
  - description of value.
  - actual path in the helm values
  - if required in all or some deployments
  - mark sensitive or non sensitive
  - option for default values
- Possibly this will require a statefile that can be shared with customers.
- This state file should be shareable with customers and they should be able to
    - add deployments
    - Manage actual values in each deployments
    - should support sensitive values in secure manner
    - Should keep provision to fetch the sensitive data from secret manager or some other places.
- When helm chart has updates, will need to support addition, modification or deletion of any of the value config. So like a feature to merge statefiles may be.

## Implementation
- Helm plugin can be developed with python and typer
- How to name and what kind of statefiles if required to be maintained, please help me decide.
