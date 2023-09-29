# Vedro Flaky Steps Plugin

## How to install?

To install plugin, follow these steps:

Using pip:

```shell
$ pip install git+https://github.com/miner34006/vedro-flaky-steps@main

OR

$ pip install vedro-flaky-steps
```

Using Vedro plugin manager:

```shell
$ vedro plugin install vedro-allure-reporter
```

## How to use?

First you need to deactivate rerunner plugin and activate vedro-flakys-steps plugin (reruns are available with same `--reruns` option)

```python
# ./vedro.cfg.py
import vedro
import vedro.plugins.rerunner as rerunner
import vedro_flaky_steps as flaker

class Config(vedro.Config):

    class Plugins(vedro.Config.Plugins):

        class Rerunner(rerunner.Rerunner):
            enabled = False

        class FlakySteps(flaker.FlakySteps):
            enabled = True
```

Then you can use `@expected_failure` decorator in your Vedro scenarios:
```python
class Scenario(vedro.Scenario):
    @expected_failure('.*random.randint.*', continue_on_error=True, comment='your message here')
    def your_flaky_step(self):
        assert random.randint(0, 1)
```


## Behaviour

`expected_failure` has 3 options:

- `expected_error_regexp` - regular expression to find your expected flaky error.
- `continue_on_error` - flag that tells the plugin whether to perform further steps, when met expected flaky error. If set to `True` the next step will be executed when flaky step failed with expected error. If set to `False` scenario will be finished on that step (scenario will have a success status).
- `comment` - any information that will be printed in case expected flaky error was met.

After all scenarios have been finished, summary will be displayed in case at least one flaky error was met:
```
# 1 expected errors met in 1 scenarios, 1 errors skipped
```
