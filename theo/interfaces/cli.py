# from argparse_prompt import PromptParser
import argparse
import code
import getpass
from web3 import Web3
from theo.version import __version__
from theo.scanner import exploits_from_mythril
from theo.file import exploits_from_file
from theo import private_key_to_account


def main():
    parser = argparse.ArgumentParser(
        description="Monitor contracts for balance changes or tx pool.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # RPC connection type
    # Required HTTP connection
    parser.add_argument(
        "--rpc-http", help="Connect to this HTTP RPC", default="http://127.0.0.1:8545"
    )
    # Optional connections
    rpc = parser.add_argument_group("RPC connections")
    rpc.add_argument("--rpc-ws", help="Connect to this WebSockets RPC", default=None)
    rpc.add_argument("--rpc-ipc", help="Connect to this IPC RPC", default=None)

    # Account to use for attacking
    parser.add_argument("--account-pk", help="The account's private key")

    # Contract to monitor
    parser.add_argument(
        "--contract", help="Contract to interact with", metavar="ADDRESS"
    )

    # Find exploits with Mythril
    parser.add_argument(
        "--skip-mythril",
        help="Skip scanning the contract with Mythril",
        default=False,
        action="store_true",
    )

    # Load exploits from file
    parser.add_argument(
        "--load-file", type=str, help="Load exploit from file", default=""
    )

    # Print version and exit
    parser.add_argument(
        "--version", action="version", version="Version: {}".format(__version__)
    )

    # Parse all arguments
    args = parser.parse_args()

    # Get account from the private key
    if args.account_pk is None:
        args.account_pk = getpass.getpass(
            prompt="The account's private key (input hidden)\n> "
        )
    args.account = private_key_to_account(args.account_pk)

    if args.contract is None:
        args.contract = input("Contract to interact with\n> ")

    args.contract = Web3.toChecksumAddress(args.contract)
    args.account = Web3.toChecksumAddress(args.account)

    start_repl(args)


def start_repl(args):
    exploits = []

    # Transactions to frontrun
    if args.skip_mythril is False:
        print(
            "Scanning for exploits in contract: {contract}".format(
                contract=args.contract
            )
        )
        exploits += exploits_from_mythril(
            rpcHTTP=args.rpc_http,
            rpcWS=args.rpc_ws,
            rpcIPC=args.rpc_ipc,
            contract=args.contract,
            account_pk=args.account_pk,
        )
    if args.load_file != "":
        exploits += exploits_from_file(
            file=args.load_file,
            rpcHTTP=args.rpc_http,
            rpcWS=args.rpc_ws,
            rpcIPC=args.rpc_ipc,
            contract=args.contract,
            account_pk=args.account_pk,
        )

    if len(exploits) == 0:
        print("No exploits found. You're going to need to load some exploits.")
    else:
        print("Found exploits(s):\n", exploits)

    # Create a web3 instance
    w3 = Web3(Web3.HTTPProvider(args.rpc_http))

    # Load history
    history_path = "./.theo_history"

    def save_history(historyPath=history_path):
        import readline

        readline.write_history_file(history_path)

    import os
    import readline
    if os.path.isfile(history_path):
        readline.read_history_file(history_path)
    # Trigger history save on exit
    import atexit
    atexit.register(save_history)
    # Load variables
    vars = globals()
    vars.update(locals())
    # Start REPL
    import rlcompleter
    readline.set_completer(rlcompleter.Completer(vars).complete)
    readline.parse_and_bind("tab: complete")
    del os, atexit, readline, rlcompleter, save_history
    code.InteractiveConsole(vars).interact(
        banner="""
A few objects are available in the console:
- `exploits` is an array of loaded exploits found by Mythril or read from a file
- `w3` an initialized instance of web3py for the provided HTTP RPC endpoint

Check the readme for more info:
https://github.com/cleanunicorn/theo
"""
    )

    print("Shutting down")
