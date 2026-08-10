"""Seed idempotente de `government_periods` (nível federal).

Datas de posse são registro histórico público — não são estatística
sujeita a fonte/metodologia como os indicadores, por isso não passam pelo
fluxo de sync com SyncRun. Servem apenas como referência visual discreta
nos gráficos históricos (ver regra: nunca usar cor de partido, nunca tratar
o presidente como protagonista do gráfico).

Uso: python -m app.sync.seed_government_periods
"""
from datetime import date

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.government_period import GovernmentLevel, GovernmentPeriod
from app.sync.upsert import get_or_create_brasil, get_state

# Governadores estaduais (1995–vigente), um período por titular efetivo —
# trocas no meio do mandato (cassação, renúncia, morte, vice assume) viram
# dois registros separados, com a data exata da troca, mesma convenção já
# usada no nível federal (ver FEDERAL_PERIODS: Dilma Rousseff → Michel
# Temer em 2016-08-31).
#
# Fonte: páginas "Lista de governadores de/do <estado>" da Wikipédia em
# português (uma pesquisa por estado, cruzando com as páginas por mandato
# quando necessário) — é uma fonte secundária, não um órgão oficial,
# diferente de todas as outras datas usadas no IFB. Mantido aqui só como
# registro histórico público de baixo risco de disputa factual (quem
# ocupou o cargo e quando), não como estatística — mesma regra do nível
# federal: nunca cor de partido, nunca tratar o titular como protagonista.
#
# Um pequeno número de datas de troca no meio do mandato não teve o dia
# exato confirmado em mais de uma fonte (diferença de 1 dia entre a data
# de assinatura da renúncia e a data de posse do sucessor) — usa-se a
# data mais citada, sem impacto relevante em indicadores anuais/mensais.
STATE_GOVERNORS: dict[str, list[tuple[str, date, date | None]]] = {
    "AC": [
        ("Orleir Cameli", date(1995, 1, 1), date(1999, 1, 1)),
        ("Jorge Viana", date(1999, 1, 1), date(2003, 1, 1)),
        ("Jorge Viana", date(2003, 1, 1), date(2007, 1, 1)),
        ("Binho Marques", date(2007, 1, 1), date(2011, 1, 1)),
        ("Tião Viana", date(2011, 1, 1), date(2015, 1, 1)),
        ("Tião Viana", date(2015, 1, 1), date(2019, 1, 1)),
        ("Gladson Cameli", date(2019, 1, 1), date(2023, 1, 1)),
        ("Gladson Cameli", date(2023, 1, 1), date(2026, 4, 2)),
        ("Mailza Assis", date(2026, 4, 2), None),
    ],
    "AL": [
        ("Divaldo Suruagy", date(1995, 1, 1), date(1997, 7, 17)),
        ("Manoel Gomes de Barros", date(1997, 7, 17), date(1999, 1, 1)),
        ("Ronaldo Lessa", date(1999, 1, 1), date(2003, 1, 1)),
        ("Ronaldo Lessa", date(2003, 1, 1), date(2006, 3, 31)),
        ("Luís Abílio de Sousa Neto", date(2006, 3, 31), date(2007, 1, 1)),
        ("Teotônio Vilela Filho", date(2007, 1, 1), date(2011, 1, 1)),
        ("Teotônio Vilela Filho", date(2011, 1, 1), date(2015, 1, 1)),
        ("Renan Filho", date(2015, 1, 1), date(2019, 1, 1)),
        ("Renan Filho", date(2019, 1, 1), date(2022, 4, 2)),
        ("Klever Loureiro", date(2022, 4, 2), date(2022, 5, 15)),
        ("Paulo Dantas", date(2022, 5, 15), date(2022, 10, 11)),
        ("José Wanderley Neto", date(2022, 10, 11), date(2022, 10, 24)),
        ("Paulo Dantas", date(2022, 10, 24), date(2023, 1, 1)),
        ("Paulo Dantas", date(2023, 1, 1), None),
    ],
    "AP": [
        ("João Capiberibe", date(1995, 1, 1), date(1999, 1, 1)),
        ("João Capiberibe", date(1999, 1, 1), date(2002, 4, 5)),
        ("Dalva Figueiredo", date(2002, 4, 5), date(2003, 1, 1)),
        ("Waldez Góes", date(2003, 1, 1), date(2007, 1, 1)),
        ("Waldez Góes", date(2007, 1, 1), date(2010, 4, 5)),
        ("Pedro Paulo Dias", date(2010, 4, 5), date(2011, 1, 1)),
        ("Camilo Capiberibe", date(2011, 1, 1), date(2015, 1, 1)),
        ("Waldez Góes", date(2015, 1, 1), date(2019, 1, 1)),
        ("Waldez Góes", date(2019, 1, 1), date(2023, 1, 1)),
        ("Clécio Luís", date(2023, 1, 1), None),
    ],
    "AM": [
        ("Amazonino Mendes", date(1995, 1, 1), date(1999, 1, 1)),
        ("Amazonino Mendes", date(1999, 1, 1), date(2003, 1, 1)),
        ("Eduardo Braga", date(2003, 1, 1), date(2007, 1, 1)),
        ("Eduardo Braga", date(2007, 1, 1), date(2010, 3, 31)),
        ("Omar Aziz", date(2010, 3, 31), date(2011, 1, 1)),
        ("Omar Aziz", date(2011, 1, 1), date(2014, 4, 4)),
        ("José Melo", date(2014, 4, 4), date(2015, 1, 1)),
        ("José Melo", date(2015, 1, 1), date(2017, 5, 9)),
        ("David Almeida", date(2017, 5, 9), date(2017, 10, 4)),
        ("Amazonino Mendes", date(2017, 10, 4), date(2019, 1, 1)),
        ("Wilson Lima", date(2019, 1, 1), date(2023, 1, 1)),
        ("Wilson Lima", date(2023, 1, 1), date(2026, 4, 4)),
        ("Roberto Cidade", date(2026, 4, 4), None),
    ],
    "BA": [
        ("Paulo Souto", date(1995, 1, 1), date(1999, 1, 1)),
        ("César Borges", date(1999, 1, 1), date(2002, 4, 5)),
        ("Otto Alencar", date(2002, 4, 5), date(2003, 1, 1)),
        ("Paulo Souto", date(2003, 1, 1), date(2007, 1, 1)),
        ("Jaques Wagner", date(2007, 1, 1), date(2011, 1, 1)),
        ("Jaques Wagner", date(2011, 1, 1), date(2015, 1, 1)),
        ("Rui Costa", date(2015, 1, 1), date(2019, 1, 1)),
        ("Rui Costa", date(2019, 1, 1), date(2023, 1, 1)),
        ("Jerônimo Rodrigues", date(2023, 1, 1), None),
    ],
    "CE": [
        ("Tasso Jereissati", date(1995, 1, 1), date(1999, 1, 1)),
        ("Tasso Jereissati", date(1999, 1, 1), date(2002, 4, 5)),
        ("Beni Veras", date(2002, 4, 5), date(2003, 1, 1)),
        ("Lúcio Alcântara", date(2003, 1, 1), date(2007, 1, 1)),
        ("Cid Gomes", date(2007, 1, 1), date(2011, 1, 1)),
        ("Cid Gomes", date(2011, 1, 1), date(2015, 1, 1)),
        ("Camilo Santana", date(2015, 1, 1), date(2019, 1, 1)),
        ("Camilo Santana", date(2019, 1, 1), date(2023, 1, 1)),
        ("Elmano de Freitas", date(2023, 1, 1), None),
    ],
    "DF": [
        ("Cristovam Buarque", date(1995, 1, 1), date(1999, 1, 1)),
        ("Joaquim Roriz", date(1999, 1, 1), date(2003, 1, 1)),
        ("Joaquim Roriz", date(2003, 1, 1), date(2006, 3, 31)),
        ("Maria de Lourdes Abadia", date(2006, 3, 31), date(2007, 1, 1)),
        ("José Roberto Arruda", date(2007, 1, 1), date(2010, 2, 11)),
        ("Paulo Octávio", date(2010, 2, 11), date(2010, 2, 23)),
        ("Wilson Lima", date(2010, 2, 23), date(2010, 4, 19)),
        ("Rogério Rosso", date(2010, 4, 19), date(2011, 1, 1)),
        ("Agnelo Queiroz", date(2011, 1, 1), date(2015, 1, 1)),
        ("Rodrigo Rollemberg", date(2015, 1, 1), date(2019, 1, 1)),
        ("Ibaneis Rocha", date(2019, 1, 1), date(2023, 1, 1)),
        ("Ibaneis Rocha", date(2023, 1, 1), date(2023, 1, 9)),
        ("Celina Leão", date(2023, 1, 9), date(2023, 3, 15)),
        ("Ibaneis Rocha", date(2023, 3, 15), date(2026, 3, 28)),
        ("Celina Leão", date(2026, 3, 30), None),
    ],
    "ES": [
        ("Vitor Buaiz", date(1995, 1, 1), date(1999, 1, 1)),
        ("José Ignácio Ferreira", date(1999, 1, 1), date(2003, 1, 1)),
        ("Paulo Hartung", date(2003, 1, 1), date(2007, 1, 1)),
        ("Paulo Hartung", date(2007, 1, 1), date(2011, 1, 1)),
        ("Renato Casagrande", date(2011, 1, 1), date(2015, 1, 1)),
        ("Paulo Hartung", date(2015, 1, 1), date(2019, 1, 1)),
        ("Renato Casagrande", date(2019, 1, 1), date(2023, 1, 1)),
        ("Renato Casagrande", date(2023, 1, 1), date(2026, 4, 2)),
        ("Ricardo Ferraço", date(2026, 4, 2), None),
    ],
    "GO": [
        ("Maguito Vilela", date(1995, 1, 1), date(1998, 4, 2)),
        ("Naphtali Alves de Souza", date(1998, 4, 2), date(1999, 1, 1)),
        ("Marconi Perillo", date(1999, 1, 1), date(2003, 1, 1)),
        ("Marconi Perillo", date(2003, 1, 1), date(2006, 3, 31)),
        ("Alcides Rodrigues", date(2006, 3, 31), date(2007, 1, 1)),
        ("Alcides Rodrigues", date(2007, 1, 1), date(2011, 1, 1)),
        ("Marconi Perillo", date(2011, 1, 1), date(2015, 1, 1)),
        ("Marconi Perillo", date(2015, 1, 1), date(2018, 4, 7)),
        ("José Eliton", date(2018, 4, 7), date(2019, 1, 1)),
        ("Ronaldo Caiado", date(2019, 1, 1), date(2023, 1, 1)),
        ("Ronaldo Caiado", date(2023, 1, 1), date(2026, 3, 31)),
        ("Daniel Vilela", date(2026, 3, 31), None),
    ],
    "MA": [
        ("Roseana Sarney", date(1995, 1, 1), date(1999, 1, 1)),
        ("Roseana Sarney", date(1999, 1, 1), date(2002, 4, 5)),
        ("José Reinaldo Tavares", date(2002, 4, 5), date(2003, 1, 1)),
        ("José Reinaldo Tavares", date(2003, 1, 1), date(2007, 1, 1)),
        ("Jackson Lago", date(2007, 1, 1), date(2009, 3, 4)),
        ("Roseana Sarney", date(2009, 4, 17), date(2011, 1, 1)),
        ("Roseana Sarney", date(2011, 1, 1), date(2015, 1, 1)),
        ("Flávio Dino", date(2015, 1, 1), date(2019, 1, 1)),
        ("Flávio Dino", date(2019, 1, 1), date(2022, 4, 2)),
        ("Carlos Brandão", date(2022, 4, 2), date(2023, 1, 1)),
        ("Carlos Brandão", date(2023, 1, 1), None),
    ],
    "MT": [
        ("Dante de Oliveira", date(1995, 1, 1), date(1999, 1, 1)),
        ("Dante de Oliveira", date(1999, 1, 1), date(2002, 4, 6)),
        ("Rogério Salles", date(2002, 4, 6), date(2003, 1, 1)),
        ("Blairo Maggi", date(2003, 1, 1), date(2007, 1, 1)),
        ("Blairo Maggi", date(2007, 1, 1), date(2010, 3, 31)),
        ("Silval Barbosa", date(2010, 3, 31), date(2011, 1, 1)),
        ("Silval Barbosa", date(2011, 1, 1), date(2015, 1, 1)),
        ("Pedro Taques", date(2015, 1, 1), date(2019, 1, 1)),
        ("Mauro Mendes", date(2019, 1, 1), date(2023, 1, 1)),
        ("Mauro Mendes", date(2023, 1, 1), date(2026, 3, 31)),
        ("Otaviano Pivetta", date(2026, 3, 31), None),
    ],
    "MS": [
        ("Wilson Barbosa Martins", date(1995, 1, 1), date(1999, 1, 1)),
        ("Zeca do PT (José Orcírio Miranda dos Santos)", date(1999, 1, 1), date(2003, 1, 1)),
        ("Zeca do PT (José Orcírio Miranda dos Santos)", date(2003, 1, 1), date(2007, 1, 1)),
        ("André Puccinelli", date(2007, 1, 1), date(2011, 1, 1)),
        ("André Puccinelli", date(2011, 1, 1), date(2015, 1, 1)),
        ("Reinaldo Azambuja", date(2015, 1, 1), date(2019, 1, 1)),
        ("Reinaldo Azambuja", date(2019, 1, 1), date(2023, 1, 1)),
        ("Eduardo Riedel", date(2023, 1, 1), None),
    ],
    "MG": [
        ("Itamar Franco", date(1995, 1, 1), date(1999, 1, 1)),
        ("Aécio Neves", date(1999, 1, 1), date(2003, 1, 1)),
        ("Aécio Neves", date(2003, 1, 1), date(2007, 1, 1)),
        ("Aécio Neves", date(2007, 1, 1), date(2010, 3, 31)),
        ("Antonio Anastasia", date(2010, 3, 31), date(2011, 1, 1)),
        ("Antonio Anastasia", date(2011, 1, 1), date(2014, 4, 4)),
        ("Alberto Pinto Coelho", date(2014, 4, 4), date(2015, 1, 1)),
        ("Fernando Pimentel", date(2015, 1, 1), date(2019, 1, 1)),
        ("Romeu Zema", date(2019, 1, 1), date(2023, 1, 1)),
        ("Romeu Zema", date(2023, 1, 1), date(2026, 3, 22)),
        ("Mateus Simões", date(2026, 3, 22), None),
    ],
    "PA": [
        ("Almir Gabriel", date(1995, 1, 1), date(1999, 1, 1)),
        ("Almir Gabriel", date(1999, 1, 1), date(2003, 1, 1)),
        ("Simão Jatene", date(2003, 1, 1), date(2007, 1, 1)),
        ("Ana Júlia Carepa", date(2007, 1, 1), date(2011, 1, 1)),
        ("Simão Jatene", date(2011, 1, 1), date(2015, 1, 1)),
        ("Simão Jatene", date(2015, 1, 1), date(2019, 1, 1)),
        ("Helder Barbalho", date(2019, 1, 1), date(2023, 1, 1)),
        ("Helder Barbalho", date(2023, 1, 1), date(2026, 4, 2)),
        ("Hana Ghassan", date(2026, 4, 2), None),
    ],
    "PB": [
        ("Antônio Mariz", date(1995, 1, 1), date(1995, 9, 16)),
        ("José Maranhão", date(1995, 9, 16), date(1999, 1, 1)),
        ("José Maranhão", date(1999, 1, 1), date(2002, 4, 6)),
        ("Roberto Paulino", date(2002, 4, 6), date(2003, 1, 1)),
        ("Cássio Cunha Lima", date(2003, 1, 1), date(2007, 1, 1)),
        ("Cássio Cunha Lima", date(2007, 1, 1), date(2009, 2, 17)),
        ("José Maranhão", date(2009, 2, 17), date(2011, 1, 1)),
        ("Ricardo Coutinho", date(2011, 1, 1), date(2015, 1, 1)),
        ("Ricardo Coutinho", date(2015, 1, 1), date(2019, 1, 1)),
        ("João Azevêdo", date(2019, 1, 1), date(2023, 1, 1)),
        ("João Azevêdo", date(2023, 1, 1), date(2026, 4, 2)),
        ("Lucas Ribeiro", date(2026, 4, 2), None),
    ],
    "PR": [
        ("Jaime Lerner", date(1995, 1, 1), date(1999, 1, 1)),
        ("Jaime Lerner", date(1999, 1, 1), date(2003, 1, 1)),
        ("Roberto Requião", date(2003, 1, 1), date(2006, 9, 4)),
        ("Hermas Brandão", date(2006, 9, 4), date(2007, 1, 1)),
        ("Roberto Requião", date(2007, 1, 1), date(2010, 4, 1)),
        ("Orlando Pessuti", date(2010, 4, 1), date(2011, 1, 1)),
        ("Beto Richa", date(2011, 1, 1), date(2015, 1, 1)),
        ("Beto Richa", date(2015, 1, 1), date(2018, 4, 6)),
        ("Cida Borghetti", date(2018, 4, 6), date(2019, 1, 1)),
        ("Ratinho Júnior", date(2019, 1, 1), date(2023, 1, 1)),
        ("Ratinho Júnior", date(2023, 1, 1), None),
    ],
    "PE": [
        ("Miguel Arraes", date(1995, 1, 1), date(1999, 1, 1)),
        ("Jarbas Vasconcelos", date(1999, 1, 1), date(2003, 1, 1)),
        ("Jarbas Vasconcelos", date(2003, 1, 1), date(2006, 3, 31)),
        ("Mendonça Filho", date(2006, 3, 31), date(2007, 1, 1)),
        ("Eduardo Campos", date(2007, 1, 1), date(2011, 1, 1)),
        ("Eduardo Campos", date(2011, 1, 1), date(2014, 4, 4)),
        ("João Lyra Neto", date(2014, 4, 4), date(2015, 1, 1)),
        ("Paulo Câmara", date(2015, 1, 1), date(2019, 1, 1)),
        ("Paulo Câmara", date(2019, 1, 1), date(2023, 1, 1)),
        ("Raquel Lyra", date(2023, 1, 1), None),
    ],
    "PI": [
        ("Mão Santa (Francisco de Assis de Moraes Souza)", date(1995, 1, 1), date(1999, 1, 1)),
        ("Mão Santa (Francisco de Assis de Moraes Souza)", date(1999, 1, 1), date(2001, 11, 19)),
        ("Hugo Napoleão", date(2001, 11, 19), date(2003, 1, 1)),
        ("Wellington Dias", date(2003, 1, 1), date(2007, 1, 1)),
        ("Wellington Dias", date(2007, 1, 1), date(2011, 1, 1)),
        ("Wilson Martins", date(2011, 1, 1), date(2014, 4, 4)),
        ("Antônio José de Moraes Souza Filho", date(2014, 4, 4), date(2015, 1, 1)),
        ("Wellington Dias", date(2015, 1, 1), date(2019, 1, 1)),
        ("Wellington Dias", date(2019, 1, 1), date(2022, 3, 31)),
        ("Regina Sousa", date(2022, 3, 31), date(2023, 1, 1)),
        ("Rafael Fonteles", date(2023, 1, 1), None),
    ],
    "RJ": [
        ("Marcello Alencar", date(1995, 1, 1), date(1999, 1, 1)),
        ("Anthony Garotinho", date(1999, 1, 1), date(2002, 4, 6)),
        ("Benedita da Silva", date(2002, 4, 6), date(2003, 1, 1)),
        ("Rosinha Garotinho", date(2003, 1, 1), date(2007, 1, 1)),
        ("Sérgio Cabral", date(2007, 1, 1), date(2011, 1, 1)),
        ("Sérgio Cabral", date(2011, 1, 1), date(2014, 4, 4)),
        ("Luiz Fernando Pezão", date(2014, 4, 4), date(2015, 1, 1)),
        ("Luiz Fernando Pezão", date(2015, 1, 1), date(2018, 11, 29)),
        ("Francisco Dornelles", date(2018, 11, 29), date(2019, 1, 1)),
        ("Wilson Witzel", date(2019, 1, 1), date(2020, 8, 28)),
        ("Cláudio Castro", date(2020, 8, 28), date(2023, 1, 1)),
        ("Cláudio Castro", date(2023, 1, 1), date(2026, 3, 23)),
        ("Ricardo Couto de Castro", date(2026, 3, 23), None),
    ],
    "RN": [
        ("Garibaldi Alves Filho", date(1995, 1, 1), date(1999, 1, 1)),
        ("Garibaldi Alves Filho", date(1999, 1, 1), date(2002, 4, 6)),
        ("Fernando Freire", date(2002, 4, 6), date(2003, 1, 1)),
        ("Wilma de Faria", date(2003, 1, 1), date(2007, 1, 1)),
        ("Wilma de Faria", date(2007, 1, 1), date(2010, 3, 31)),
        ("Iberê Ferreira", date(2010, 3, 31), date(2011, 1, 1)),
        ("Rosalba Ciarlini", date(2011, 1, 1), date(2015, 1, 1)),
        ("Robinson Faria", date(2015, 1, 1), date(2019, 1, 1)),
        ("Fátima Bezerra", date(2019, 1, 1), date(2023, 1, 1)),
        ("Fátima Bezerra", date(2023, 1, 1), None),
    ],
    "RS": [
        ("Antônio Britto", date(1995, 1, 1), date(1999, 1, 1)),
        ("Olívio Dutra", date(1999, 1, 1), date(2003, 1, 1)),
        ("Germano Rigotto", date(2003, 1, 1), date(2007, 1, 1)),
        ("Yeda Crusius", date(2007, 1, 1), date(2011, 1, 1)),
        ("Tarso Genro", date(2011, 1, 1), date(2015, 1, 1)),
        ("José Ivo Sartori", date(2015, 1, 1), date(2019, 1, 1)),
        ("Eduardo Leite", date(2019, 1, 1), date(2022, 3, 31)),
        ("Ranolfo Vieira Júnior", date(2022, 3, 31), date(2023, 1, 1)),
        ("Eduardo Leite", date(2023, 1, 1), None),
    ],
    "RO": [
        ("Valdir Raupp", date(1995, 1, 1), date(1999, 1, 1)),
        ("José Bianco", date(1999, 1, 1), date(2003, 1, 1)),
        ("Ivo Cassol", date(2003, 1, 1), date(2007, 1, 1)),
        ("Ivo Cassol", date(2007, 1, 1), date(2010, 3, 31)),
        ("João Cahulla", date(2010, 3, 31), date(2011, 1, 1)),
        ("Confúcio Moura", date(2011, 1, 1), date(2015, 1, 1)),
        ("Confúcio Moura", date(2015, 1, 1), date(2018, 4, 6)),
        ("Daniel Pereira", date(2018, 4, 6), date(2019, 1, 1)),
        ("Marcos Rocha", date(2019, 1, 1), date(2023, 1, 1)),
        ("Marcos Rocha", date(2023, 1, 1), None),
    ],
    "RR": [
        ("Neudo Campos", date(1995, 1, 1), date(1999, 1, 1)),
        ("Neudo Campos", date(1999, 1, 1), date(2002, 4, 6)),
        ("Flamarion Portela", date(2002, 4, 6), date(2003, 1, 1)),
        ("Flamarion Portela", date(2003, 1, 1), date(2004, 11, 10)),
        ("Ottomar Pinto", date(2004, 11, 10), date(2007, 1, 1)),
        ("Ottomar Pinto", date(2007, 1, 1), date(2007, 12, 11)),
        ("José Anchieta Júnior", date(2007, 12, 11), date(2011, 1, 1)),
        ("José Anchieta Júnior", date(2011, 1, 1), date(2014, 4, 4)),
        ("Chico Rodrigues", date(2014, 4, 4), date(2015, 1, 1)),
        ("Suely Campos", date(2015, 1, 1), date(2018, 12, 10)),
        ("Antônio Denarium", date(2018, 12, 10), date(2019, 1, 1)),
        ("Antônio Denarium", date(2019, 1, 1), date(2023, 1, 1)),
        ("Antônio Denarium", date(2023, 1, 1), date(2026, 3, 27)),
        ("Edilson Damião", date(2026, 3, 27), date(2026, 4, 30)),
        ("Soldado Sampaio", date(2026, 4, 30), None),
    ],
    "SC": [
        ("Paulo Afonso Vieira", date(1995, 1, 1), date(1999, 1, 1)),
        ("Esperidião Amin", date(1999, 1, 1), date(2003, 1, 1)),
        ("Luiz Henrique da Silveira", date(2003, 1, 1), date(2006, 4, 9)),
        ("Eduardo Pinho Moreira", date(2006, 4, 9), date(2007, 1, 1)),
        ("Luiz Henrique da Silveira", date(2007, 1, 1), date(2010, 3, 25)),
        ("Leonel Pavan", date(2010, 3, 25), date(2011, 1, 1)),
        ("Raimundo Colombo", date(2011, 1, 1), date(2015, 1, 1)),
        ("Raimundo Colombo", date(2015, 1, 1), date(2018, 4, 5)),
        ("Eduardo Pinho Moreira", date(2018, 4, 5), date(2019, 1, 1)),
        ("Carlos Moisés", date(2019, 1, 1), date(2023, 1, 1)),
        ("Jorginho Mello", date(2023, 1, 1), None),
    ],
    "SP": [
        ("Mário Covas", date(1995, 1, 1), date(1999, 1, 1)),
        ("Mário Covas", date(1999, 1, 1), date(2001, 3, 6)),
        ("Geraldo Alckmin", date(2001, 3, 6), date(2003, 1, 1)),
        ("Geraldo Alckmin", date(2003, 1, 1), date(2006, 3, 31)),
        ("Cláudio Lembo", date(2006, 3, 31), date(2007, 1, 1)),
        ("José Serra", date(2007, 1, 1), date(2010, 4, 2)),
        ("Alberto Goldman", date(2010, 4, 2), date(2011, 1, 1)),
        ("Geraldo Alckmin", date(2011, 1, 1), date(2015, 1, 1)),
        ("Geraldo Alckmin", date(2015, 1, 1), date(2018, 4, 6)),
        ("Márcio França", date(2018, 4, 6), date(2019, 1, 1)),
        ("João Doria", date(2019, 1, 1), date(2022, 3, 31)),
        ("Rodrigo Garcia", date(2022, 4, 1), date(2023, 1, 1)),
        ("Tarcísio de Freitas", date(2023, 1, 1), None),
    ],
    "SE": [
        ("Albano Franco", date(1995, 1, 1), date(1999, 1, 1)),
        ("Albano Franco", date(1999, 1, 1), date(2003, 1, 1)),
        ("João Alves Filho", date(2003, 1, 1), date(2007, 1, 1)),
        ("João Alves Filho", date(2007, 1, 1), date(2011, 1, 1)),
        ("Marcelo Déda", date(2011, 1, 1), date(2013, 12, 2)),
        ("Jackson Barreto", date(2013, 12, 2), date(2015, 1, 1)),
        ("Jackson Barreto", date(2015, 1, 1), date(2018, 4, 7)),
        ("Belivaldo Chagas", date(2018, 4, 7), date(2019, 1, 1)),
        ("Belivaldo Chagas", date(2019, 1, 1), date(2023, 1, 1)),
        ("Fábio Mitidieri", date(2023, 1, 1), None),
    ],
    "TO": [
        ("Siqueira Campos", date(1995, 1, 1), date(1998, 4, 4)),
        ("Raimundo Boi (Moisés Avelino)", date(1998, 4, 4), date(1999, 1, 1)),
        ("Siqueira Campos", date(1999, 1, 1), date(2003, 1, 1)),
        ("Marcelo Miranda", date(2003, 1, 1), date(2007, 1, 1)),
        ("Marcelo Miranda", date(2007, 1, 1), date(2009, 9, 8)),
        ("Carlos Henrique Gaguim", date(2009, 9, 9), date(2011, 1, 1)),
        ("Siqueira Campos", date(2011, 1, 1), date(2014, 4, 4)),
        ("Sandoval Cardoso", date(2014, 4, 4), date(2015, 1, 1)),
        ("Marcelo Miranda", date(2015, 1, 1), date(2018, 3, 27)),
        ("Mauro Carlesse", date(2018, 3, 27), date(2018, 4, 6)),
        ("Marcelo Miranda", date(2018, 4, 6), date(2018, 4, 19)),
        ("Mauro Carlesse", date(2018, 4, 19), date(2019, 1, 1)),
        ("Mauro Carlesse", date(2019, 1, 1), date(2022, 3, 11)),
        ("Wanderlei Barbosa", date(2022, 3, 11), date(2023, 1, 1)),
        ("Wanderlei Barbosa", date(2023, 1, 1), None),
    ],
}


def seed_state_governors() -> None:
    if not STATE_GOVERNORS:
        print("Governadores estaduais: nenhum dado carregado ainda (STATE_GOVERNORS vazio) — pulando.")
        return

    with SessionLocal() as db:
        added = 0
        for uf, periods in STATE_GOVERNORS.items():
            state = get_state(db, uf)
            if state is None:
                print(f"Governadores: UF '{uf}' não encontrada — rode seed_states antes.")
                continue

            existing = {
                (row.holder_name, row.start_date)
                for row in db.execute(
                    select(GovernmentPeriod).where(
                        GovernmentPeriod.location_id == state.id,
                        GovernmentPeriod.level == GovernmentLevel.state,
                    )
                ).scalars()
            }

            for holder_name, start_date, end_date in periods:
                if (holder_name, start_date) in existing:
                    continue
                db.add(
                    GovernmentPeriod(
                        location_id=state.id,
                        level=GovernmentLevel.state,
                        holder_name=holder_name,
                        start_date=start_date,
                        end_date=end_date,
                    )
                )
                added += 1

        db.commit()
    print(f"Governadores estaduais sincronizados ({added} período(s) novo(s)).")


FEDERAL_PERIODS = [
    ("Fernando Henrique Cardoso", date(1995, 1, 1), date(1999, 1, 1)),
    ("Fernando Henrique Cardoso", date(1999, 1, 1), date(2003, 1, 1)),
    ("Luiz Inácio Lula da Silva", date(2003, 1, 1), date(2007, 1, 1)),
    ("Luiz Inácio Lula da Silva", date(2007, 1, 1), date(2011, 1, 1)),
    ("Dilma Rousseff", date(2011, 1, 1), date(2015, 1, 1)),
    ("Dilma Rousseff", date(2015, 1, 1), date(2016, 8, 31)),
    ("Michel Temer", date(2016, 8, 31), date(2019, 1, 1)),
    ("Jair Bolsonaro", date(2019, 1, 1), date(2023, 1, 1)),
    ("Luiz Inácio Lula da Silva", date(2023, 1, 1), None),
]


def seed() -> None:
    with SessionLocal() as db:
        brasil = get_or_create_brasil(db)

        existing = {
            (row.holder_name, row.start_date)
            for row in db.execute(
                select(GovernmentPeriod).where(
                    GovernmentPeriod.location_id == brasil.id,
                    GovernmentPeriod.level == GovernmentLevel.federal,
                )
            ).scalars()
        }

        for holder_name, start_date, end_date in FEDERAL_PERIODS:
            if (holder_name, start_date) in existing:
                continue
            db.add(
                GovernmentPeriod(
                    location_id=brasil.id,
                    level=GovernmentLevel.federal,
                    holder_name=holder_name,
                    start_date=start_date,
                    end_date=end_date,
                )
            )

        db.commit()
    print("Períodos de governo federal sincronizados.")
    seed_state_governors()


if __name__ == "__main__":
    seed()
