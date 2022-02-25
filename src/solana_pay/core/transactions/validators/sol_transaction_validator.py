from solana.transaction import TransactionSignature
from solana.publickey import PublicKey
from solana_pay.common.exceptions import ValidateTransactionError
from solana_pay.common.consts import LAMPORTS_PER_SOL
from solana.rpc.api import Client
from solana.rpc.commitment import Commitment
from typing import Optional, Union, List, Dict
from solana_pay.core.transactions.validators.transaction_validator import TransactionDetails, TransactionValidator


class SolTransactionValidator(TransactionValidator):
    def __init__(self, rpc_client: Client):
        super().__init__(rpc_client)

    def __call__(self, transaction_details: TransactionDetails):
        transaction = self._rpc_client.get_transaction(
            transaction_details.signature, commitment=transaction_details.commitment).get("result")

        if transaction == None:
            raise ValidateTransactionError("Transaction was not found.")
        if transaction.get("meta") == None:
            raise ValidateTransactionError("Transaction has no meta.")
        if meta_error := transaction.get("meta").get("error"):
            raise ValidateTransactionError(meta_error)

        if str(transaction_details.recipient) in transaction["transaction"]["message"]["accountKeys"]:
            recipient_id = transaction["transaction"]["message"]["accountKeys"].index(
                str(transaction_details.recipient))
            pre_amount = transaction["meta"]["preBalances"][recipient_id] / \
                LAMPORTS_PER_SOL
            post_amount = transaction["meta"]["postBalances"][recipient_id] / \
                LAMPORTS_PER_SOL
        else:
            raise ValidateTransactionError("Recipient was not found.")

        SolTransactionValidator._validate_amount(
            pre_amount, post_amount, transaction_details.amount)
        SolTransactionValidator._validate_reference(
            transaction_details.reference, transaction["transaction"]["message"]["accountKeys"])

        return True
