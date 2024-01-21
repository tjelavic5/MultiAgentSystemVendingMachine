from spade.agent import Agent
from asyncio import sleep
from spade.behaviour import FSMBehaviour, State
from spade.message import Message
import json

class AgentCovjek(Agent):
    
    def __init__(self, jid, password, budzet):
        super().__init__(jid, password)
        self.budzet = budzet
        self.trenutnoUneseniNovac = 0.0
        
    async def setup(self):

        fsm = self.PonasanjeCovjek()

        fsm.add_state(name="Pocetak", state=self.Pocetak(), initial=True)
        fsm.add_state(name="BiranjeProizvoda", state=self.BiranjeProizvoda())
        fsm.add_state(name="Placanje", state=self.Placanje())
        fsm.add_state(name="CekanjeProizvoda", state=self.CekanjeProizvoda())
        fsm.add_state(name="DobivenProizvodIUzetOstatakNovca", state=self.DobivenProizvodIUzetOstatakNovca())

        fsm.add_transition(source="Pocetak", dest="BiranjeProizvoda")
        fsm.add_transition(source="BiranjeProizvoda", dest="BiranjeProizvoda")
        fsm.add_transition(source="BiranjeProizvoda", dest="Placanje")
        fsm.add_transition(source="Placanje", dest="CekanjeProizvoda")
        fsm.add_transition(source="CekanjeProizvoda", dest="CekanjeProizvoda")
        fsm.add_transition(source="CekanjeProizvoda", dest="BiranjeProizvoda")
        fsm.add_transition(source="CekanjeProizvoda", dest="DobivenProizvodIUzetOstatakNovca")
        fsm.add_transition(source="DobivenProizvodIUzetOstatakNovca", dest="DobivenProizvodIUzetOstatakNovca")
        fsm.add_transition(source="DobivenProizvodIUzetOstatakNovca", dest="Pocetak")

        self.add_behaviour(fsm)
    
    class PonasanjeCovjek(FSMBehaviour):
        async def on_start(self):
            print("Zapocinjem agenta covjek")
            print("Covjek: Dosao sam do automata")

        async def on_end(self):
            print("Zavrsavam agenta covjek")
            await self.agent.stop()

    class Pocetak(State):
        async def run(self):
            novaPorukaPocetak = Message(to = "agentAutomat@localhost", body = json.dumps({"porukaPocetak": True}), metadata= {"ontology": "agent"})
            await self.send(novaPorukaPocetak)
            self.set_next_state("BiranjeProizvoda")
            
    class BiranjeProizvoda(State):
        async def run(self):
            poruka = await self.receive(timeout=15)
            if poruka:
                sadrzajPoruke = json.loads(poruka.body)
                if "sviProizvodi" in sadrzajPoruke:
                    sviProizvodi = sadrzajPoruke["sviProizvodi"]
                    sveVrsteProizvoda = list(sviProizvodi["Cijene"].keys())
                    print("Trenutno se u automatu nalazi: \n")
                    formatiranjeIspisa = "{:<20} {:<15} {:<10}"
                    formatiranjeRedaka = "{:<20} {:<15.2f} {:<10} Klikni {}"
                    print(formatiranjeIspisa.format("PROIZVOD", "CIJENA", "KOLICINA"))
                    brojac = 1
                    for vrstaProizvoda in sveVrsteProizvoda:
                        print(formatiranjeRedaka.format(
                            vrstaProizvoda,
                            sviProizvodi['Cijene'][vrstaProizvoda],
                            sviProizvodi['Kolicine'][vrstaProizvoda],
                            brojac  
                        ))
                        brojac += 1
                    print("Klikni 0 za odustajanje")
                    while True:
                        odabir = input("\nUnesite broj proizvoda: ")
                        try:
                            odabirBroj = int(odabir)
                            if odabirBroj > len(sveVrsteProizvoda) or odabirBroj < 0:
                                print("Neispravan unos")
                            elif sviProizvodi['Kolicine'][sveVrsteProizvoda[odabirBroj-1]] < 1 and odabirBroj != 0:
                                print("Tog proizvoda nema, izaberite drugi")
                            else:
                                break
                        except Exception:
                            print("Neispravan unos")
                            
                    if odabirBroj > 0:        
                        odabraniProizvod = sveVrsteProizvoda[odabirBroj-1]
                        odabraniProizvodKolicine = sviProizvodi['Kolicine'][odabraniProizvod]
                        while True:
                            odabirKolicine = input("Unesite kolicinu proizvoda: ")
                            try:
                                odabirKolicineInt = int(odabirKolicine)
                                if odabraniProizvodKolicine < odabirKolicineInt:
                                    print(f"U automatu se ne nalazi {odabirKolicineInt} komada {odabraniProizvod}. Izaberite manju kolicinu")
                                elif odabirKolicineInt < 1:
                                    print("Neispravan unos")
                                else:
                                    print(f"Covjek: Odabrao sam {odabirKolicineInt} {odabraniProizvod}")
                                    break
                            except Exception:
                                print("Neispravan unos")                    
                        
                        novaPorukaPocetak = Message(to = "agentAutomat@localhost", body = json.dumps({"porukaIzboraVrstaProizvoda": odabraniProizvod, "porukaIzboraKolicinaProizvoda": odabirKolicineInt}), metadata= {"ontology": "agent"})
                        await self.send(novaPorukaPocetak)
                        self.set_next_state("Placanje")
                    else:
                        novaPorukaKraj = Message(to = "agentAutomat@localhost", body = json.dumps({"kraj": True}), metadata= {"ontology": "agent"})
                        await self.send(novaPorukaKraj)
                        print("Covjek: Odustao sam od kupnje na automatu")
                        await self.agent.stop()
                else:
                    print("Covjek: Krivi sadrzaj poruke")
                    self.set_next_state("BiranjeProizvoda")
            else:
                print("Covjek: poruka nije dosla nakon 15 s")
                self.set_next_state("BiranjeProizvoda")
                
    class Placanje(State):
        async def run(self):
            while True:
                await sleep(0.5)
                odabirNovac = input("Unesite novce: ")
                try:
                    odabirNovacFloat = float(odabirNovac)
                    if odabirNovacFloat < 0:
                        print("Neispravan unos")
                    elif self.agent.budzet < odabirNovacFloat:
                        print("Nemate toliko novaca u svom budzetu")
                    else:
                        break
                except Exception:
                    print("Neispravan unos")
            self.agent.trenutnoUneseniNovac = odabirNovacFloat
            await sleep(1)
            novaPorukaPocetak = Message(to = "agentAutomat@localhost", body = json.dumps({"novac": odabirNovacFloat}), metadata= {"ontology": "agent"})
            await self.send(novaPorukaPocetak)
            self.set_next_state("CekanjeProizvoda")
            
    class CekanjeProizvoda(State):
        async def run(self):
            poruka = await self.receive(timeout=15)
            if poruka:
                sadrzajPoruke = json.loads(poruka.body)
                if "DovoljnoNovaca" in sadrzajPoruke:
                    dovoljnoNovaca = sadrzajPoruke["DovoljnoNovaca"]
                    if dovoljnoNovaca:
                        self.set_next_state("DobivenProizvodIUzetOstatakNovca")
                    else:
                        self.set_next_state("BiranjeProizvoda")
                else:
                    print("Covjek: Krivi sadrzaj poruke")
                    self.set_next_state("CekanjeProizvoda")
            else:
                print("Covjek: poruka nije dosla nakon 15 s")
                self.set_next_state("CekanjeProizvoda")
                
    class DobivenProizvodIUzetOstatakNovca(State):
        async def run(self):
            poruka = await self.receive(timeout=15)
            if poruka:
                sadrzajPoruke = json.loads(poruka.body)
                if "Ostatak" in sadrzajPoruke:
                    ostatakNovaca = sadrzajPoruke["Ostatak"]
                    print("Covjek: Uzeo sam proizvod")
                    if ostatakNovaca > 0:
                        print(f"Covjek: Uzeo sam ostatak novca koji iznosi {ostatakNovaca}")
                    self.agent.budzet -= self.agent.trenutnoUneseniNovac - ostatakNovaca
                    print(f"Vas trenutni budzet je {self.agent.budzet:.2f}")
                else:
                    print("Covjek: Krivi sadrzaj poruke")
                    self.set_next_state("DobivenProizvodIUzetOstatakNovca")
            else:
                print("Covjek: Poruka nije dosla nakon 15 s")
                self.set_next_state("DobivenProizvodIUzetOstatakNovca")
            ponovnaKupovina = input ("Zelite li jos kupovati? da / ne: ")
            if ponovnaKupovina == "da":
                await sleep(2)
                self.set_next_state("Pocetak")
            else:
                print("Covjek: Odlazim")