from argparse import ArgumentParser
from spade import wait_until_finished, run
from agentautomat import AgentAutomat
from agentcovjek import AgentCovjek

async def main(brojAgenataCovjek):
    agentAutomat = AgentAutomat(jid = "agentAutomat@localhost", password = "agentAutomat")
    await agentAutomat.start()
    
    for i in range(brojAgenataCovjek):
        print("Zapocinje covjek:", i+1)
        while True:
            budzetIznos = input("Unesite budzet: ")
            try:
                odabirBudzet = float(budzetIznos)
                if odabirBudzet < 5:
                    print("Premali budzet")
                else:
                    break
            except Exception:
                print("Neispravan unos")
        agentCovjek = AgentCovjek(jid = f"agentCovjek{i+1}@localhost", password = f"agentCovjek{i+1}", budzet = odabirBudzet)
        await agentCovjek.start()
        await wait_until_finished(agentCovjek)
        
    await agentAutomat.stop()
    print("Zavrsavam agenta automat")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-brojAgenataCovjek", type = int, help = "Broj agenata covjek koji ce se pokreniti")
    args = parser.parse_args()
    run (main(args.brojAgenataCovjek))