<a name="aea.helpers.preference_representations.base"></a>
# aea.helpers.preference`_`representations.base

Preference representation helpers.

<a name="aea.helpers.preference_representations.base.logarithmic_utility"></a>
#### logarithmic`_`utility

```python
logarithmic_utility(utility_params_by_good_id: Dict[str, float], quantities_by_good_id: Dict[str, int], quantity_shift: int = 100) -> float
```

Compute agent's utility given her utility function params and a good bundle.

**Arguments**:

- `utility_params_by_good_id`: utility params by good identifier
- `quantities_by_good_id`: quantities by good identifier
- `quantity_shift`: a non-negative factor to shift the quantities in the utility function (to ensure the natural logarithm can be used on the entire range of quantities)

**Returns**:

utility value

<a name="aea.helpers.preference_representations.base.linear_utility"></a>
#### linear`_`utility

```python
linear_utility(exchange_params_by_currency_id: Dict[str, float], balance_by_currency_id: Dict[str, int]) -> float
```

Compute agent's utility given her utility function params and a good bundle.

**Arguments**:

- `exchange_params_by_currency_id`: exchange params by currency
- `balance_by_currency_id`: balance by currency

**Returns**:

utility value

