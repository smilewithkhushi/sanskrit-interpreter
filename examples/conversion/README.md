# English to Sanskrit conversion examples

These examples use small in-memory datasets to show code patterns that are useful in applications. Each `.english.skt` file is the source for its matching `.sanskrit.skt` file. The converted file keeps comments, string labels, indentation, and user-defined names.

| Pair | Scenario | Expected result |
| --- | --- | --- |
| `inventory_reorder` | Compute a sorted reorder list, including stock entries that are missing | Reorder 6 of A-100 and 5 of C-300 |
| `invoice_cents` | Validate invoice values and calculate a discounted total in integer cents | Total: 4522 cents |
| `service_health` | Classify service samples with an explicit threshold and invalid-sample case | API healthy, worker alert, scheduler invalid |

From the project root, preview a conversion:

```sh
python3 -m sanskrit_repl --to-sanskrit examples/conversion/inventory_reorder.english.skt
```

To write a separate converted file, add `--output`:

```sh
python3 -m sanskrit_repl --to-sanskrit examples/conversion/inventory_reorder.english.skt --output /tmp/inventory_reorder.skt
```

Run either version with `python3 -m sanskrit_repl`, for example:

```sh
python3 -m sanskrit_repl examples/conversion/invoice_cents.sanskrit.skt
```

In VS Code, open an English file and run **Sanskrit REPL: Convert English Syntax to Sanskrit** from the Command Palette. Review the unsaved preview beside the source before saving it.

These are self-contained examples. Real inventory, billing, and monitoring systems would supply their data through a separate integration layer; this interpreter does not provide file, network, or database access.
