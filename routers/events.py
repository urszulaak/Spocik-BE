from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
import models
import schemas
from database import get_db
from routers.users import get_current_user
from typing import List, Optional
from datetime import date
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

router = APIRouter(
    prefix="/api/events",
    tags=["Wydarzenia"]
)

@router.get("", response_model=List[schemas.EventResponse])
def get_events(
    date: Optional[date] = None,
    week: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Event)
    
    if date:
        query = query.filter(models.Event.date == date)
    if week:
        query = query.filter(models.Event.week == week)
    if year:
        query = query.filter(models.Event.year == year)
        
    events = query.all()
    
    for event in events:
        event._links = {
            "self": {"href": f"/api/events/{event.id}", "method": "GET"}
        }
    return events

@router.get("/report")
def generate_events_report(
    db: Session = Depends(get_db)
):
    events = db.query(models.Event).order_by(models.Event.date).all()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title = Paragraph("Zestawienie Wydarzen - Spocik", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    data = [["Data", "Nazwa", "Kategoria", "Opis"]]
    for event in events:
        data.append([
            str(event.date),
            str(event.name),
            str(event.type),
            str(event.description or "")
        ])
        
    table = Table(data, colWidths=[60, 120, 80, 200])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return Response(
        content=pdf_bytes, 
        media_type="application/pdf", 
        headers={"Content-Disposition": "attachment; filename=raport_wydarzen.pdf"}
    )

@router.get("/{event_id}", response_model=schemas.EventResponse)
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Wydarzenie nie istnieje")
        
    event._links = {
        "self": {"href": f"/api/events/{event.id}", "method": "GET"},
        "update": {"href": f"/api/events/{event.id}", "method": "PUT"},
        "delete": {"href": f"/api/events/{event.id}", "method": "DELETE"},
        "pdf_report": {"href": "/api/events/report", "method": "GET"},
        "all_events": {"href": "/api/events", "method": "GET"}
    }
    
    return event

@router.post("", response_model=schemas.EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_in: schemas.EventCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    event_dict = event_in.model_dump()
    
    # Calculate week, month, year from date
    event_date = event_dict['date']
    event_dict['week'] = event_date.isocalendar()[1]
    event_dict['month'] = event_date.month
    event_dict['year'] = event_date.year
    event_dict['author_id'] = current_user.id
    
    new_event = models.Event(**event_dict)
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    new_event._links = {
        "self": {"href": f"/api/events/{new_event.id}", "method": "GET"}
    }
    return new_event

@router.put("/{event_id}", response_model=schemas.EventResponse)
def update_event(
    event_id: str,
    event_update: schemas.EventUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wydarzenie nie istnieje")

    if not current_user.is_admin and str(event.author_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Brak uprawnień. Tylko autor lub administrator może edytować to wydarzenie."
        )

    update_data = event_update.model_dump(exclude_unset=True)
    
    if 'date' in update_data:
        event_date = update_data['date']
        update_data['week'] = event_date.isocalendar()[1]
        update_data['month'] = event_date.month
        update_data['year'] = event_date.year

    for key, value in update_data.items():
        setattr(event, key, value)
        
    db.commit()
    db.refresh(event)
    
    event._links = {
        "self": {"href": f"/api/events/{event.id}", "method": "GET"}
    }
    return event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: str, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wydarzenie nie istnieje")

    if not current_user.is_admin:
        if str(event.author_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Brak uprawnień. Tylko autor lub administrator może usunąć to wydarzenie."
            )

    db.delete(event)
    db.commit()
    
    return