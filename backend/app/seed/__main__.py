"""Entry point so ``python -m app.seed`` runs the seeder."""

import sys

from app.seed.run_seed import main

if __name__ == "__main__":
    sys.exit(main())
