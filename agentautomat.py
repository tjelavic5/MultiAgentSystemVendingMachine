from spade.agent import Agent
from asyncio import sleep
from spade.behaviour import FSMBehaviour, State
from spade.message import Message
import json

class AgentAutomat(Agent):
    
    def __init__(self, jid, password):
        super().__init__(jid, password)
        proizvodiCijene = {
            "Coca-Cola": 2.2, 
            "Fanta": 1.5, 
            "Pepsi": 2.1, 
            "CedevitaNaranča": 2.1, 
            "CedevitaLimun": 2.1,
            "Sprite": 1.7,
            "Sok od jabuke": 1.8,
            "Voda": 1.0,
            "Gazirana voda": 1.1,
            "Energetsko piće": 2.5,
            "Iced Tea": 1.6,
            "Ledena kava": 2.3,
            "Bezalkoholno pivo": 2.0,
            "Sportski napitak": 2.2,
        }
        proizvodiKolicine = {
            "Coca-Cola": 5, 
            "Fanta": 9, 
            "Pepsi": 7, 
            "CedevitaNaranča": 0, 
            "CedevitaLimun": 3,
            "Sprite": 7,
            "Sok od jabuke": 4,
            "Voda": 2,
            "Gazirana voda": 1,
            "Energetsko piće": 2,
            "Iced Tea": 6,
            "Ledena kava": 3,
            "Bezalkoholno pivo": 4,
            "Sportski napitak": 2,
        }
        self.proizvodi = {"Cijene": proizvodiCijene, "Kolicine": proizvodiKolicine}
        self.jidCovjeka = ""
        self.odabraniProizvod = ""
        self.odabranaKolicina = 0
        self.ukupnaCijenaTrenutnogProizvoda = 0
        self.uplaceniNovac = 0


    class PonasanjeAutomat(FSMBehaviour):
        async def on_start(self):
            print("Zapocinjem agenta automat")

        async def on_end(self):
            print("Zavrsavam agenta automat")
            await self.agent.stop()
        

    async def setup(self):

        fsm = self.PonasanjeAutomat()

        fsm.add_state(name="CekanjeCovjeka", state=self.CekanjeCovjeka(), initial=True)
        fsm.add_state(name="CekanjeOdabiraCovjeka", state=self.CekanjeOdabiraCovjeka())
        fsm.add_state(name="CekaNovac", state=self.CekaNovac())
        fsm.add_state(name="DajeProizvodIVracaOstatakNovca", state=self.DajeProizvodIVracaOstatakNovca())

        fsm.add_transition(source="CekanjeCovjeka", dest="CekanjeCovjeka")
        fsm.add_transition(source="CekanjeCovjeka", dest="CekanjeOdabiraCovjeka")
        fsm.add_transition(source="CekanjeOdabiraCovjeka", dest="CekanjeOdabiraCovjeka")
        fsm.add_transition(source="CekanjeOdabiraCovjeka", dest="CekaNovac")
        fsm.add_transition(source="CekanjeOdabiraCovjeka", dest="CekanjeCovjeka")
        fsm.add_transition(source="CekaNovac", dest="CekaNovac")
        fsm.add_transition(source="CekaNovac", dest="CekanjeOdabiraCovjeka")
        fsm.add_transition(source="CekaNovac", dest="DajeProizvodIVracaOstatakNovca")
        fsm.add_transition(source="DajeProizvodIVracaOstatakNovca", dest="CekanjeCovjeka")

        self.add_behaviour(fsm)

    class CekanjeCovjeka(State):
        async def run(self):
            self.agent.jidCovjeka = ""
            self.agent.odabraniProizvod = ""
            self.agent.kupnaCijenaTrenutnogProizvoda = 0
            self.agent.uplaceniNovac = 0
            print("Automat: Cekam covjeka")
            poruka = await self.receive(timeout=10)
            if poruka:
                sadrzajPoruke = json.loads(poruka.body)
                if "porukaPocetak" in sadrzajPoruke:
                    self.agent.jidCovjeka = str(poruka.sender)
                    novaPorukaPocetak = Message(to = self.agent.jidCovjeka, body = json.dumps({"sviProizvodi": self.agent.proizvodi}), metadata= {"ontology": "agent"})
                    await self.send(novaPorukaPocetak)
                    self.set_next_state("CekanjeOdabiraCovjeka")
                else:
                    print("Automat: Krivi sadrzaj poruke")
                    self.set_next_state("CekanjeCovjeka")
            else:
                print("Automat: Poruka nije dosla nakon 10 s")
                self.set_next_state("CekanjeCovjeka")
                
    class CekanjeOdabiraCovjeka(State):
        async def run(self):
            print("Automat: Cekam izbor covjeka")
            poruka = await self.receive(timeout=50)
            if poruka:
                sadrzajPoruke = json.loads(poruka.body)
                if "porukaIzboraVrstaProizvoda" in sadrzajPoruke:
                    vrstaProizvoda = sadrzajPoruke["porukaIzboraVrstaProizvoda"] 
                    kolicinaProizvoda = sadrzajPoruke["porukaIzboraKolicinaProizvoda"] 
                    self.agent.ukupnaCijenaTrenutnogProizvoda = round(self.agent.proizvodi["Cijene"][vrstaProizvoda] * kolicinaProizvoda, 2)
                    self.agent.odabraniProizvod = vrstaProizvoda
                    self.agent.odabranaKolicina = kolicinaProizvoda
                    print("Automat: Ukupan iznos je:", self.agent.ukupnaCijenaTrenutnogProizvoda)
                    self.set_next_state("CekaNovac")
                elif "kraj" in sadrzajPoruke:
                    self.set_next_state("CekanjeCovjeka")
                else:
                    print("sadrzajPoruke", sadrzajPoruke)
                    self.set_next_state("CekanjeOdabiraCovjeka")
            else:
                print("Automat: Poruka nije dosla nakon 50 s")
                self.set_next_state("CekanjeOdabiraCovjeka")
                
    class CekaNovac(State):
        async def run(self):
            print("Automat: Cekam novac")
            poruka = await self.receive(timeout=20)
            if poruka:
                sadrzajPoruke = json.loads(poruka.body)
                if "novac" in sadrzajPoruke:
                    kolicinaNovca = sadrzajPoruke["novac"]
                    if kolicinaNovca >= self.agent.ukupnaCijenaTrenutnogProizvoda:
                        print("Automat: Ima dovoljno novaca")
                        self.agent.uplaceniNovac = kolicinaNovca
                        novaPorukaDovoljnoNovaca = Message(to = self.agent.jidCovjeka, body = json.dumps({"DovoljnoNovaca": True}), metadata= {"ontology": "agent"})
                        await self.send(novaPorukaDovoljnoNovaca)
                        self.set_next_state("DajeProizvodIVracaOstatakNovca")
                    else:
                        print("Automat: Iznos:", kolicinaNovca, " nije dovoljan. Ukupna cijena je:", self.agent.ukupnaCijenaTrenutnogProizvoda)
                        print("Automat: Vracam uneseni novac. Izaberite novi proizvod")
                        novaPorukaDovoljnoNovaca = Message(to = self.agent.jidCovjeka, body = json.dumps({"DovoljnoNovaca": False}), metadata= {"ontology": "agent"})
                        await self.send(novaPorukaDovoljnoNovaca)
                        await sleep(1)
                        novaPorukaPocetak = Message(to = self.agent.jidCovjeka, body = json.dumps({"sviProizvodi": self.agent.proizvodi}), metadata= {"ontology": "agent"})
                        await self.send(novaPorukaPocetak)
                        self.set_next_state("CekanjeOdabiraCovjeka")
                else:
                    self.set_next_state("CekaNovac")
            else:
                print("Automat: Poruka nije dosla nakon 20 s")
                self.set_next_state("CekaNovac")
                
    class DajeProizvodIVracaOstatakNovca(State):
        async def run(self):
            print("Automat: Dajem proizvod:", self.agent.odabranaKolicina, self.agent.odabraniProizvod)
            self.agent.proizvodi["Kolicine"][self.agent.odabraniProizvod] -= self.agent.odabranaKolicina
            if self.agent.proizvodi["Kolicine"][self.agent.odabraniProizvod] < 1:
                print("Automat: Ponestalo je:", self.agent.odabraniProizvod)
                self.agent.proizvodi["Kolicine"][self.agent.odabraniProizvod] = 0
            ostatakNovca = round(self.agent.uplaceniNovac - self.agent.ukupnaCijenaTrenutnogProizvoda, 2)
            if ostatakNovca > 0:
                print("Automat: Vracam ostatak novca koji iznosi:", ostatakNovca)
            novaPorukaPoslano = Message(to = self.agent.jidCovjeka, body = json.dumps({"Ostatak": ostatakNovca}), metadata= {"ontology": "agent"})
            await self.send(novaPorukaPoslano)
            await sleep(1)
            self.set_next_state("CekanjeCovjeka")