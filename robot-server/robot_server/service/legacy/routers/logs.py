from fastapi import APIRouter, Query, Response

from opentrons.system import log_control
from robot_server.service.legacy.models.logs import LogIdentifier, LogFormat

router = APIRouter()


@router.get("/logs/{log_identifier}", description="Get logs from the robot.")
async def get_logs(
    log_identifier: LogIdentifier,
    format: LogFormat = Query(LogFormat.text, title="Log format type"),
    records: int = Query(
        log_control.DEFAULT_RECORDS, title="Number of records to retrieve",
        gt=0, le=log_control.MAX_RECORDS
    ),
) -> Response:
    identifier = 'opentrons-api-serial'
    if log_identifier == LogIdentifier.api:
        identifier = 'opentrons-api'

    modes = {LogFormat.json: ("json", "application/json"),
             LogFormat.text: ("short", "text/plain")}
    format_type, media_type = modes[format]
    output = await log_control.get_records_dumb(
        identifier, records, format_type
    )
    return Response(
        content=output.decode('utf-8'), media_type=media_type)
