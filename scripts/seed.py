import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.use_cases import CreateCustomerUseCase, UpdateCustomerStatusUseCase
from app.domain.entities import CustomerStatus
from app.domain.errors import EmailAlreadyExistsError
from app.infrastructure.database import Database
from app.infrastructure.database.models import CustomerModel
from app.infrastructure.repositories import SqlAlchemyCustomerRepository
from app.shared.logging import configure_logging

logger = logging.getLogger("seed")

DEMO_CUSTOMERS: list[tuple[str, str, CustomerStatus]] = [
    ("Juan Pérez", "juan.perez@example.com", CustomerStatus.ACTIVE),
    ("María García", "maria.garcia@example.com", CustomerStatus.ACTIVE),
    ("Carlos López", "carlos.lopez@example.com", CustomerStatus.PENDING),
    ("Ana Martínez", "ana.martinez@example.com", CustomerStatus.BLOCKED),
    ("Luis Hernández", "luis.hernandez@example.com", CustomerStatus.ACTIVE),
    ("Sofía Rodríguez", "sofia.rodriguez@example.com", CustomerStatus.PENDING),
    ("Diego Torres", "diego.torres@example.com", CustomerStatus.ACTIVE),
    ("Valentina Ruiz", "valentina.ruiz@example.com", CustomerStatus.ACTIVE),
    ("Javier Morales", "javier.morales@example.com", CustomerStatus.BLOCKED),
    ("Camila Flores", "camila.flores@example.com", CustomerStatus.PENDING),
    ("Andrés Castillo", "andres.castillo@example.com", CustomerStatus.ACTIVE),
    ("Lucía Ortiz", "lucia.ortiz@example.com", CustomerStatus.ACTIVE),
    ("Mateo Jiménez", "mateo.jimenez@example.com", CustomerStatus.PENDING),
    ("Isabella Vargas", "isabella.vargas@example.com", CustomerStatus.ACTIVE),
    ("Sebastián Romero", "sebastian.romero@example.com", CustomerStatus.BLOCKED),
    ("Daniela Navarro", "daniela.navarro@example.com", CustomerStatus.ACTIVE),
    ("Fernando Silva", "fernando.silva@corp.com", CustomerStatus.PENDING),
    ("Gabriela Mendoza", "gabriela.mendoza@corp.com", CustomerStatus.ACTIVE),
    ("Ricardo Guzmán", "ricardo.guzman@corp.com", CustomerStatus.ACTIVE),
    ("Paula Rojas", "paula.rojas@corp.com", CustomerStatus.PENDING),
    ("Tomás Aguilar", "tomas.aguilar@corp.com", CustomerStatus.ACTIVE),
    ("Natalia Herrera", "natalia.herrera@corp.com", CustomerStatus.BLOCKED),
    ("Emilio Cruz", "emilio.cruz@corp.com", CustomerStatus.ACTIVE),
    ("Renata Delgado", "renata.delgado@corp.com", CustomerStatus.PENDING),
    ("Héctor Ramos", "hector.ramos@corp.com", CustomerStatus.ACTIVE),
]


def _backdate(session: Session, customer_id: UUID, created_at: datetime) -> None:
    model = session.get(CustomerModel, customer_id)
    if model is not None:
        model.created_at = created_at
        session.commit()


def main() -> None:
    configure_logging("INFO")
    session = Database.instance().session()
    repository = SqlAlchemyCustomerRepository(session)
    create_customer = CreateCustomerUseCase(repository)
    update_status = UpdateCustomerStatusUseCase(repository)
    created = 0
    try:
        now = datetime.now(UTC)
        for index, (name, email, status) in enumerate(DEMO_CUSTOMERS):
            try:
                customer = create_customer.execute(name=name, email=email)
            except EmailAlreadyExistsError:
                continue
            if status is not CustomerStatus.PENDING:
                update_status.execute(customer.id, status)
            _backdate(session, customer.id, now - timedelta(days=(index * 11) % 29, hours=index % 9))
            created += 1
    finally:
        session.close()
        Database.close()
    logger.info("Seed finished: %s created, %s skipped", created, len(DEMO_CUSTOMERS) - created)


if __name__ == "__main__":
    main()
