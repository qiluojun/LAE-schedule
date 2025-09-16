"""
LAE v2.0 示例数据创建脚本
生成三个顶级 domain 节点及其层级结构和一些 activity types
"""

import os
import sys
from datetime import datetime, date
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal
from app.models.models import Domain, ActivityType, Schedule, ScheduledEvent

def create_sample_domains():
    """创建示例 domains (领域)"""
    db = SessionLocal()

    # 顶级 domains
    research_domain = Domain(
        name="Research Projects",
        description="Academic and professional research activities"
    )

    development_domain = Domain(
        name="Software Development",
        description="Programming and technical development projects"
    )

    personal_domain = Domain(
        name="Personal Growth",
        description="Learning, skills development, and personal projects"
    )

    db.add_all([research_domain, development_domain, personal_domain])
    db.commit()

    # Research Projects 子域
    zeropPD = Domain(
        name="zeroPPD",
        description="Zero-shot Paper Processing and Discovery project",
        parent_id=research_domain.id
    )

    literature_review = Domain(
        name="Literature Review",
        description="Systematic literature review activities",
        parent_id=zeropPD.id
    )

    data_analysis = Domain(
        name="Data Analysis",
        description="Statistical analysis and data processing",
        parent_id=zeropPD.id
    )

    paper_writing = Domain(
        name="Paper Writing",
        description="Academic writing and publication preparation",
        parent_id=zeropPD.id
    )

    # Development 子域
    lae_system = Domain(
        name="LAE System",
        description="Personal Schedule and Task Management System",
        parent_id=development_domain.id
    )

    lae_schedule = Domain(
        name="LAE-Schedule",
        description="Core scheduling functionality",
        parent_id=lae_system.id
    )

    lae_reminder = Domain(
        name="LAE-Reminder",
        description="Reminder and notification system",
        parent_id=lae_system.id
    )

    # Personal Growth 子域
    skill_development = Domain(
        name="Skill Development",
        description="Learning new skills and technologies",
        parent_id=personal_domain.id
    )

    health_fitness = Domain(
        name="Health & Fitness",
        description="Physical and mental health activities",
        parent_id=personal_domain.id
    )

    db.add_all([
        zeropPD, literature_review, data_analysis, paper_writing,
        lae_system, lae_schedule, lae_reminder,
        skill_development, health_fitness
    ])
    db.commit()

    print("Sample domains created successfully!")
    return db

def create_sample_activity_types():
    """创建示例 activity types (活动类型)"""
    db = SessionLocal()

    # 顶级活动类型
    intellectual_work = ActivityType(
        name="Intellectual Work",
        description="Cognitive and analytical tasks"
    )

    communication = ActivityType(
        name="Communication",
        description="Writing, presenting, and discussing"
    )

    implementation = ActivityType(
        name="Implementation",
        description="Hands-on execution and building"
    )

    learning = ActivityType(
        name="Learning",
        description="Knowledge acquisition and skill development"
    )

    db.add_all([intellectual_work, communication, implementation, learning])
    db.commit()

    # Intellectual Work 子类型
    reading = ActivityType(
        name="Reading",
        description="Reading papers, documentation, books",
        parent_id=intellectual_work.id
    )

    analysis = ActivityType(
        name="Analysis",
        description="Data analysis, code review, critical thinking",
        parent_id=intellectual_work.id
    )

    planning = ActivityType(
        name="Planning",
        description="Strategic planning and design thinking",
        parent_id=intellectual_work.id
    )

    # Communication 子类型
    writing = ActivityType(
        name="Writing",
        description="Document creation, paper writing, blogging",
        parent_id=communication.id
    )

    presentation = ActivityType(
        name="Presentation",
        description="Preparing and giving presentations",
        parent_id=communication.id
    )

    discussion = ActivityType(
        name="Discussion",
        description="Meetings, brainstorming, collaboration",
        parent_id=communication.id
    )

    # Implementation 子类型
    coding = ActivityType(
        name="Coding",
        description="Programming and software development",
        parent_id=implementation.id
    )

    testing = ActivityType(
        name="Testing",
        description="Testing, debugging, and quality assurance",
        parent_id=implementation.id
    )

    deployment = ActivityType(
        name="Deployment",
        description="System deployment and configuration",
        parent_id=implementation.id
    )

    # Learning 子类型
    research = ActivityType(
        name="Research",
        description="Information gathering and exploration",
        parent_id=learning.id
    )

    tutorial = ActivityType(
        name="Tutorial",
        description="Following tutorials and courses",
        parent_id=learning.id
    )

    practice = ActivityType(
        name="Practice",
        description="Hands-on practice and exercises",
        parent_id=learning.id
    )

    db.add_all([
        reading, analysis, planning,
        writing, presentation, discussion,
        coding, testing, deployment,
        research, tutorial, practice
    ])
    db.commit()

    print("Sample activity types created successfully!")
    return db

def create_sample_schedules():
    """创建一些示例 schedules"""
    db = SessionLocal()

    # 获取一些 domains 用于关联
    zeropPD = db.query(Domain).filter(Domain.name == "zeroPPD").first()
    lae_schedule = db.query(Domain).filter(Domain.name == "LAE-Schedule").first()

    if zeropPD:
        schedule1 = Schedule(
            domain_id=zeropPD.id,
            name="Complete Literature Review Phase 1",
            description="Review 20 papers on storyline extraction methods",
            deadline=datetime(2025, 10, 15),
            status="ongoing"
        )
        db.add(schedule1)

    if lae_schedule:
        schedule2 = Schedule(
            domain_id=lae_schedule.id,
            name="LAE v2.0 Development Milestone",
            description="Implement core v2.0 features and UI redesign",
            deadline=datetime(2025, 9, 30),
            status="ongoing"
        )
        db.add(schedule2)

    db.commit()
    print("Sample schedules created successfully!")
    return db

def create_sample_data():
    """创建所有示例数据"""
    print("Creating LAE v2.0 sample data...")

    db = create_sample_domains()
    db.close()

    db = create_sample_activity_types()
    db.close()

    db = create_sample_schedules()
    db.close()

    print("All sample data created successfully!")
    print("\nSample data includes:")
    print("- 3 top-level domains with hierarchical sub-domains")
    print("- 4 top-level activity types with sub-categories")
    print("- Example schedules linked to domains")

if __name__ == "__main__":
    create_sample_data()