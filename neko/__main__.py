import asyncio

from .main import main as amain

def main() -> int:
    return asyncio.run(amain())

if __name__ == '__main__':
    exit(main())