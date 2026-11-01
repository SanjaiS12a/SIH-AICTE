"""Reproduce fictional upload fixtures; these are demonstrations, not training labels."""
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parent
TODAY = datetime.now(timezone(timedelta(hours=5, minutes=30))).replace(hour=10, minute=0, second=0, microsecond=0)


def row(reference, bureau, category, summary, days=1, status='registered', institution='SIH-26264-DEMO'):
    received = TODAY-timedelta(days=days)
    return {'source_reference':reference, 'institution_permanent_id':institution, 'bureau':bureau, 'category':category,
        'summary':summary, 'description':summary+' Fictional SIH demonstration only; no real complainant or institution allegation.',
        'received_at':received.isoformat(), 'status':status, 'incident_date':received.date().isoformat(),
        'due_at':(received+timedelta(days=30)).isoformat(),
        'disposed_at':(TODAY-timedelta(days=15)).isoformat() if status=='disposed' else '',
        'resolution_note':'Fictional verification completed; original documents returned.' if status=='disposed' else '',
        'source_system':'sih-starter-'+bureau.lower(),
        'classification':'regulatory_compliance' if category=='facilities' else 'grievance'}


def save(name, rows):
    fields=list(rows[0])
    with (ROOT/(name+'.csv')).open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    book=Workbook();sheet=book.active;sheet.title='Complaints';sheet.append(fields)
    for value in rows:sheet.append(list(value.values()))
    sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
    for column in sheet.columns:sheet.column_dimensions[column[0].column_letter].width=26
    book.save(ROOT/(name+'.xlsx'))


if __name__=='__main__':
    examples=[row('TRAIN-REFUND-2026-A','RB','refunds','The diploma applicant withdrew in September 2026 under TRAIN-REFUND-2026-A but has not received the fee refund. Please verify repayment.',status='under_review'),
        row('TRAIN-REFUND-2026-A','PGRC','refunds','Fees for the September 2026 diploma withdrawal remain unpaid. Reference TRAIN-REFUND-2026-A requests the same refund.'),
        row('TRAIN-REFUND-2025-B','RB','refunds','A different applicant requests the hostel-deposit refund for the 2025 academic year under TRAIN-REFUND-2025-B.',days=60),
        row('TRAIN-LAB-SAFETY','DEMO','facilities','The mechanical laboratory emergency exit is locked. Please obtain a signed safety inspection report.',days=45,status='awaiting_response'),
        row('TRAIN-SCHOLARSHIP','PGRC','scholarships','The sanctioned merit scholarship has not reached the student. Please verify the disbursement record.'),
        row('TRAIN-DOCUMENTS','RB','documents','Original academic documents retained after withdrawal have now been returned to the applicant.',days=60,status='disposed')]
    examples[0]['incident_date']=examples[1]['incident_date']='2026-09-15'
    examples[2]['incident_date']='2025-07-01'
    save('start-here-6-cases',examples)
    templates=[('refunds','Tuition fees remain unpaid after admission cancellation'),('admissions','The admission cancellation record needs a written response'),
        ('documents','Original certificates have not been returned after withdrawal'),('facilities','Laboratory safety equipment requires inspection'),
        ('scholarships','The sanctioned scholarship payment requires verification'),('administration','The examination record correction requires a written response')]
    load=[]
    for n in range(1000):
        category,text=templates[n%6]
        item=row(f'LOAD-{n+1:04d}', ['RB','PGRC','DEMO'][n%3],category,
            f'{text} for fictional incident LOAD-{n+1:04d}. Please verify institutional records.',
            days=1+n%60,institution=f'DEMO-{1+n%30:04d}')
        item['source_system']='sih-starter-load';load.append(item)
    save('load-test-1000-cases',load)
    assert len(examples)==6 and len(load)==1000
    assert len({(r['source_system'],r['source_reference']) for r in examples})==6
    print('Created six-case walkthrough and 1,000-row load fixtures, each as XLSX and CSV.')
