# Riemann Framework
# Copyright (C) 2026 MILAN NIKOLIC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import sys
from pathlib import Path


if __package__ in {None, ""}:
	sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from riemann_framework.plots import plot_explicit_formula, plot_zeros_complex


def main() -> None:
	"""Generate the complex-zero and explicit-formula plots."""
	print("Generating zero plot...")
	plot_zeros_complex()

	print("Generating explicit-formula plot...")
	plot_explicit_formula()

	print("Finished!")


if __name__ == "__main__":
	main()