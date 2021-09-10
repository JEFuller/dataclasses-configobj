# dataclasses-configobj

Hydrate Data Classes from `ini`/`dat`/toml files.

Aims to be [`dataclasses-json`](https://github.com/lidatong/dataclasses-json), but for [`configobj`](https://github.com/DiffSK/configobj).

This is _very alpha_ right now, but the feaures which work, should work:

## Usage

Define the shape of your config:

* Each subsection will be mapped to a nested class
* Each subsection may define a single `_many`
* A `_many` must have type `List[...]`
* The type of `List` of a `_many` shall have a `_name`

Example:

```python
@dataclass
class Single:
    other: str

@dataclass
class OneOfMany:
    _name: str
    val: str

@dataclass
class Config:
    single: Single
    _many: List[OneOfMany]
    optional: Optional[str] = None
```

To load this `.ini` file:

```
[single]
other = hello
[one]
val = apple
[two]
val = banana
```

We can read, validate, and `lift` to an instance of `Config` with:

```pythonfrom dataclasses_configobj import lift, to_specj import to_spec, lift


spec = core.to_spec(Config)
co = configobj.ConfigObj(infile=infile, configspec=spec)

validator = validate.Validator()
co.validate(validator)

config: Config = dataclasses.lift(Config, co)
```

To yield `config`:
```
Config(
    single=Single(other='hello'),
    optional=None,
    withdefault='test123'
    _many=[
        OneOfMany(_name='one', val='apple'),
        OneOfMany(_name='two', val='banana')
    ]
)