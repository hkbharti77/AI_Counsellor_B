"""
Database Seed Script
Populate database with sample university data
"""
from database import SessionLocal, engine, Base
from models import University
import json

# Sample university data
UNIVERSITIES = [
    {
        "name": "Massachusetts Institute of Technology (MIT)",
        "country": "USA",
        "city": "Cambridge, MA",
        "ranking": 1,
        "tuition_min": 53000,
        "tuition_max": 58000,
        "programs": json.dumps(["Computer Science", "Engineering", "Business", "Physics", "Mathematics"]),
        "acceptance_rate": 4.0,
        "ielts_requirement": 7.0,
        "gre_requirement": 330,
        "toefl_requirement": 100,
        "application_deadline": "January 1",
        "image_url": "https://images.unsplash.com/photo-1564981797816-1043664bf78d?w=400",
        "description": "World-leading research university known for science, engineering, and technology."
    },
    {
        "name": "Stanford University",
        "country": "USA",
        "city": "Stanford, CA",
        "ranking": 3,
        "tuition_min": 54000,
        "tuition_max": 60000,
        "programs": json.dumps(["Computer Science", "Business", "Law", "Medicine", "Engineering"]),
        "acceptance_rate": 4.3,
        "ielts_requirement": 7.0,
        "gre_requirement": 330,
        "toefl_requirement": 100,
        "application_deadline": "January 5",
        "image_url": "https://images.unsplash.com/photo-1541625247028-8e14c89c6c08?w=400",
        "description": "Elite research university in Silicon Valley with strong entrepreneurship culture."
    },
    {
        "name": "University of California, Berkeley",
        "country": "USA",
        "city": "Berkeley, CA",
        "ranking": 15,
        "tuition_min": 43000,
        "tuition_max": 48000,
        "programs": json.dumps(["Computer Science", "Engineering", "Business", "Data Science", "Public Policy"]),
        "acceptance_rate": 17.0,
        "ielts_requirement": 6.5,
        "gre_requirement": 320,
        "toefl_requirement": 90,
        "application_deadline": "December 1",
        "image_url": "https://images.unsplash.com/photo-1607237138185-eedd9c632b0b?w=400",
        "description": "Top public university known for engineering and computer science programs."
    },
    {
        "name": "University of Toronto",
        "country": "Canada",
        "city": "Toronto, ON",
        "ranking": 25,
        "tuition_min": 32000,
        "tuition_max": 40000,
        "programs": json.dumps(["Computer Science", "Engineering", "Business", "Life Sciences", "Arts"]),
        "acceptance_rate": 43.0,
        "ielts_requirement": 6.5,
        "gre_requirement": 310,
        "toefl_requirement": 89,
        "application_deadline": "January 15",
        "image_url": "https://images.unsplash.com/photo-1569012871812-f38ee64cd54c?w=400",
        "description": "Canada's top university with diverse programs and strong research output."
    },
    {
        "name": "Technical University of Munich (TUM)",
        "country": "Germany",
        "city": "Munich",
        "ranking": 50,
        "tuition_min": 500,
        "tuition_max": 2000,
        "programs": json.dumps(["Engineering", "Computer Science", "Natural Sciences", "Management"]),
        "acceptance_rate": 35.0,
        "ielts_requirement": 6.5,
        "gre_requirement": 310,
        "toefl_requirement": 88,
        "application_deadline": "May 31",
        "image_url": "https://images.unsplash.com/photo-1590846406792-0adc7f938f1d?w=400",
        "description": "Germany's top technical university with nearly free tuition for international students."
    },
    {
        "name": "Imperial College London",
        "country": "UK",
        "city": "London",
        "ranking": 6,
        "tuition_min": 35000,
        "tuition_max": 45000,
        "programs": json.dumps(["Engineering", "Medicine", "Science", "Business", "Computing"]),
        "acceptance_rate": 14.0,
        "ielts_requirement": 7.0,
        "gre_requirement": 320,
        "toefl_requirement": 100,
        "application_deadline": "January 15",
        "image_url": "https://images.unsplash.com/photo-1526129318478-62ed807ebdf9?w=400",
        "description": "World-class science and engineering university in central London."
    },
    {
        "name": "ETH Zurich",
        "country": "Switzerland",
        "city": "Zurich",
        "ranking": 8,
        "tuition_min": 1000,
        "tuition_max": 2000,
        "programs": json.dumps(["Engineering", "Computer Science", "Natural Sciences", "Architecture"]),
        "acceptance_rate": 27.0,
        "ielts_requirement": 7.0,
        "gre_requirement": 320,
        "toefl_requirement": 100,
        "application_deadline": "December 15",
        "image_url": "https://images.unsplash.com/photo-1530122037265-a5f1f91d3b99?w=400",
        "description": "Top European university known for science, tech, and low tuition fees."
    },
    {
        "name": "National University of Singapore (NUS)",
        "country": "Singapore",
        "city": "Singapore",
        "ranking": 11,
        "tuition_min": 18000,
        "tuition_max": 25000,
        "programs": json.dumps(["Computing", "Business", "Engineering", "Law", "Medicine"]),
        "acceptance_rate": 28.0,
        "ielts_requirement": 6.5,
        "gre_requirement": 315,
        "toefl_requirement": 92,
        "application_deadline": "January 15",
        "image_url": "https://images.unsplash.com/photo-1565967511849-76a60a516170?w=400",
        "description": "Asia's leading university with strong industry connections and research."
    },
    {
        "name": "University of Melbourne",
        "country": "Australia",
        "city": "Melbourne",
        "ranking": 33,
        "tuition_min": 35000,
        "tuition_max": 45000,
        "programs": json.dumps(["Business", "Engineering", "Arts", "Science", "Medicine"]),
        "acceptance_rate": 45.0,
        "ielts_requirement": 6.5,
        "gre_requirement": 300,
        "toefl_requirement": 79,
        "application_deadline": "October 31",
        "image_url": "https://images.unsplash.com/photo-1514395462725-fb4566210144?w=400",
        "description": "Australia's top university with excellent student life and diverse programs."
    },
    {
        "name": "University of British Columbia",
        "country": "Canada",
        "city": "Vancouver, BC",
        "ranking": 35,
        "tuition_min": 28000,
        "tuition_max": 38000,
        "programs": json.dumps(["Computer Science", "Engineering", "Business", "Forestry", "Sciences"]),
        "acceptance_rate": 52.0,
        "ielts_requirement": 6.5,
        "gre_requirement": 300,
        "toefl_requirement": 90,
        "application_deadline": "January 15",
        "image_url": "https://images.unsplash.com/photo-1580777361964-27e9cdd2f838?w=400",
        "description": "Beautiful campus university with strong programs and high acceptance rate."
    },
    {
        "name": "Georgia Institute of Technology",
        "country": "USA",
        "city": "Atlanta, GA",
        "ranking": 45,
        "tuition_min": 33000,
        "tuition_max": 38000,
        "programs": json.dumps(["Computer Science", "Engineering", "Business", "Sciences"]),
        "acceptance_rate": 21.0,
        "ielts_requirement": 7.0,
        "gre_requirement": 320,
        "toefl_requirement": 95,
        "application_deadline": "January 1",
        "image_url": "https://images.unsplash.com/photo-1562774053-701939374585?w=400",
        "description": "Top-tier engineering school with strong industry partnerships."
    },
    {
        "name": "University of Texas at Austin",
        "country": "USA",
        "city": "Austin, TX",
        "ranking": 40,
        "tuition_min": 38000,
        "tuition_max": 42000,
        "programs": json.dumps(["Computer Science", "Engineering", "Business", "Law", "Liberal Arts"]),
        "acceptance_rate": 32.0,
        "ielts_requirement": 6.5,
        "gre_requirement": 315,
        "toefl_requirement": 79,
        "application_deadline": "December 1",
        "image_url": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=400",
        "description": "Major research university in the tech hub of Austin."
    },
    {
        "name": "University of Waterloo",
        "country": "Canada",
        "city": "Waterloo, ON",
        "ranking": 112,
        "tuition_min": 25000,
        "tuition_max": 35000,
        "programs": json.dumps(["Computer Science", "Engineering", "Mathematics", "Co-op Programs"]),
        "acceptance_rate": 55.0,
        "ielts_requirement": 6.5,
        "gre_requirement": 300,
        "toefl_requirement": 90,
        "application_deadline": "February 1",
        "image_url": "https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?w=400",
        "description": "Known for co-op programs and strong tech industry connections."
    },
    {
        "name": "Arizona State University",
        "country": "USA",
        "city": "Tempe, AZ",
        "ranking": 185,
        "tuition_min": 28000,
        "tuition_max": 32000,
        "programs": json.dumps(["Engineering", "Business", "Computer Science", "Design", "Journalism"]),
        "acceptance_rate": 88.0,
        "ielts_requirement": 6.0,
        "gre_requirement": 290,
        "toefl_requirement": 61,
        "application_deadline": "Rolling",
        "image_url": "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=400",
        "description": "Large public university with high acceptance and diverse programs."
    },
    {
        "name": "RWTH Aachen University",
        "country": "Germany",
        "city": "Aachen",
        "ranking": 90,
        "tuition_min": 300,
        "tuition_max": 1000,
        "programs": json.dumps(["Engineering", "Computer Science", "Natural Sciences", "Medicine"]),
        "acceptance_rate": 40.0,
        "ielts_requirement": 6.5,
        "gre_requirement": 300,
        "toefl_requirement": 80,
        "application_deadline": "March 1",
        "image_url": "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=400",
        "description": "Top German technical university with virtually free tuition."
    }
]


def seed_database():
    """Seed database with sample data"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if universities already exist
        existing = db.query(University).count()
        if existing > 0:
            print(f"Database already has {existing} universities. Skipping seed.")
            return
        
        # Add universities
        for uni_data in UNIVERSITIES:
            university = University(**uni_data)
            db.add(university)
        
        db.commit()
        print(f"✅ Successfully seeded {len(UNIVERSITIES)} universities!")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
