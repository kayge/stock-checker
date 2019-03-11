# stock-checker
An anonymized version of a recent side-project to demonstrate my ability to write python tools that are ugly, but effective!

*NOTE: This script will not run as-is, since most of the necessary guts have been [redacted].*

The basic idea was to scan a product page for changes every minute (essentially running a diff on a specific region of html), then send texts/emails to interested parties to provide notifications of specific items going in or out of stock, or to alert me if errors occurred.

This ran on an old spare laptop 24/7 for a while, and the laptop would occasionally lose its wifi connection for some unknown reason... so there's a little bonus hack in there for toggling the wireless adapter when this happened :)
