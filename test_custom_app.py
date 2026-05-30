"""
Tests for our custom application(custom_app.py).

How these tests work :
- We build the matching circuit for Alice and Bob.
- We run the real protocol: a server plus one process per party.
- We check that the compatibility score the parties compute matches the score we worked out by hand.

the rule of the app:
overlap = number of interests where BOTH put a 1
score   = overlap * POINTS_PER_MATCH

So if we know each pair of answers, we can compute the expected score by hand
and compare. 
Run all of these with:   pytest test_custom_app.py
"""

import time
from multiprocessing import Process, Queue

from expression import Scalar, Secret
from protocol import ProtocolSpec
from server import run

from smc_party import SMCParty

# Pull the same settings the app uses, so the tests stay in sync with it.
from custom_app import POINTS_PER_MATCH, INTERESTS


PORT = 63456


# start a server and the party processes, collect their results.
# This is copied from test_integration.py (just with my own PORT).

def smc_client(client_id, prot, value_dict, queue):
    cli = SMCParty(
        client_id,
        "localhost",
        PORT,
        protocol_spec=prot,
        value_dict=value_dict
    )
    res = cli.run()
    queue.put(res)
    print(f"{client_id} has finished!")


def smc_server(args):
    run("localhost", PORT, args)


def run_processes(server_args, *client_args):
    queue = Queue()

    server = Process(target=smc_server, args=(server_args,))
    clients = [Process(target=smc_client, args=(*args, queue)) for args in client_args]

    server.start()
    time.sleep(3)
    for client in clients:
        client.start()

    results = list()
    for client in clients:
        client.join()

    for client in clients:
        results.append(queue.get())

    server.terminate()
    server.join()

    time.sleep(2)
    print("Server stopped.")

    return results


# Helpers to build and run one matching scenario.

def make_secrets_and_values(answers):
    """Turn a list of 0/1 answers into Secret objects and a value dictionary."""
    secrets = []
    value_dict = {}
    for answer in answers:
        s = Secret()
        secrets.append(s)
        value_dict[s] = answer
    return secrets, value_dict


def build_score_circuit(alice_secrets, bob_secrets):
    #Build the same circuit as the app:
   # overlap = a0*b0 + a1*b1 +...+ a4*b4
    #score   = overlap*POINTS_PER_MATCH

    overlap = alice_secrets[0] * bob_secrets[0]
    for i in range(1, len(INTERESTS)):
        overlap = overlap + (alice_secrets[i] * bob_secrets[i])
    score = overlap * Scalar(POINTS_PER_MATCH)
    return score


def expected_score(alice_answers, bob_answers):
    #Work out the correct score by hand
    overlap = 0
    for i in range(len(alice_answers)):
        # A position counts only when BOTH are 1, which is exactly a*b.
        overlap = overlap + (alice_answers[i] * bob_answers[i])
    return overlap * POINTS_PER_MATCH


def run_matching_test(alice_answers, bob_answers):
    #Run the protocol for one scenario and return the list of results
    #(one per party). All parties should agree on the same number.
    
    alice_secrets, alice_values = make_secrets_and_values(alice_answers)
    bob_secrets, bob_values = make_secrets_and_values(bob_answers)

    expr = build_score_circuit(alice_secrets, bob_secrets)

    parties = {
        "Alice": alice_values,
        "Bob": bob_values,
    }
    participants = list(parties.keys())
    prot = ProtocolSpec(expr=expr, participant_ids=participants)
    clients = [(name, prot, value_dict) for name, value_dict in parties.items()]

    return run_processes(participants, *clients)


def check(alice_answers, bob_answers):
    #Run the senario and assert every party got the hand computed score
    want = expected_score(alice_answers, bob_answers)
    results = run_matching_test(alice_answers, bob_answers)
    # Both Alice and Bob must compute the exact same correct score.
    for result in results:
        assert result == want


# The actual tests. Each one is a different situation.
# Interests order: [sports, music, cooking, travel, gaming]

def test_two_shared_interests():
    # Alice: sports, music, travel   Bob: sports, travel, gaming
    # Shared: sports + travel = 2   score 20
    alice = [1, 1, 0, 1, 0]
    bob   = [1, 0, 0, 1, 1]
    check(alice, bob)


def test_no_shared_interests():
    # They like completely different things -> overlap 0 -> score 0.
    alice = [1, 1, 0, 0, 0]
    bob   = [0, 0, 1, 1, 1]
    check(alice, bob)


def test_all_shared_interests():
    # Exactly the same tastes -> overlap 5 -> score 50.
    alice = [1, 1, 1, 1, 1]
    bob   = [1, 1, 1, 1, 1]
    check(alice, bob)


def test_only_one_shared_interest():
    # They share just cooking, overlap 1, score 10.
    alice = [1, 1, 1, 0, 0]
    bob   = [0, 0, 1, 1, 1]
    check(alice, bob)


def test_alice_likes_nothing():
    # Alice answered 0 for everything, overlap must be 0, so score0.
    alice = [0, 0, 0, 0, 0]
    bob   = [1, 1, 1, 1, 1]
    check(alice, bob)


def test_both_like_nothing():
    # Nobody likes anything, overlap 0, score 0.
    alice = [0, 0, 0, 0, 0]
    bob   = [0, 0, 0, 0, 0]
    check(alice, bob)


def test_alice_full_bob_single():
    # Alice likes everything, Bob likes only cooking.
    # Overlap is just cooking = 1, score 10.
    alice = [1, 1, 1, 1, 1]
    bob   = [0, 0, 1, 0, 0]
    check(alice, bob)


def test_four_of_five_shared():
    # They agree on everything except gaming, overlap 4, score 40.
    alice = [1, 1, 1, 1, 0]
    bob   = [1, 1, 1, 1, 1]
    check(alice, bob)


def test_both_parties_agree_on_result():
    # Extra sanity check, make sure Alice and Bob compute the SAME number
    # (not just the right number). This is the whole point of SMC.
    alice = [1, 0, 1, 0, 1]
    bob   = [1, 1, 1, 0, 0]
    results = run_matching_test(alice, bob)
    # Shared: sports + cooking = 2, score 20.
    assert results[0] == 20
    # All results identical.
    assert all(r == results[0] for r in results)