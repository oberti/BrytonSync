from __future__ import annotations

import json
import struct
import time
from pathlib import Path
from typing import Any


FIT_EPOCH_OFFSET = 631065600
UINT32_INVALID = 0xFFFFFFFF
UINT8_INVALID = 0xFF


def _crc16(data: bytes) -> int:
    crc_table = [
        0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
        0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400,
    ]
    crc = 0
    for byte in data:
        tmp = crc_table[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ crc_table[byte & 0xF]

        tmp = crc_table[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ crc_table[(byte >> 4) & 0xF]
    return crc & 0xFFFF


def _fit_time_ms(ms: int | None = None) -> int:
    if ms is None:
        ms = int(time.time() * 1000)
    return int(ms / 1000) - FIT_EPOCH_OFFSET


def _def_message(local_num: int, global_num: int, fields: list[tuple[int, int, int]]) -> bytes:
    data = bytearray()
    data.append(0x40 | local_num)
    data.append(0)
    data.append(0)
    data += struct.pack("<H", global_num)
    data.append(len(fields))
    for field_num, size, base_type in fields:
        data += bytes([field_num, size, base_type])
    return bytes(data)


def _data_message(local_num: int, payload: bytes) -> bytes:
    return bytes([local_num]) + payload


def _string_field(value: str | None, size: int) -> bytes:
    value = value or ""
    raw = value.encode("utf-8", errors="ignore")[: size - 1]
    return raw + b"\x00" + (b"\x00" * (size - len(raw) - 1))


def _u8(value: int) -> bytes:
    return struct.pack("<B", value)


def _u16(value: int) -> bytes:
    return struct.pack("<H", value)


def _u32(value: int) -> bytes:
    return struct.pack("<I", value)


def _watts_to_bryton_ftp_target(watts: int | float | None, ftp: int | float | None) -> int:
    if watts is None or not ftp:
        return UINT32_INVALID

    percent = int(round(float(watts) / float(ftp) * 100))
    return 100000 + percent


def _hr_to_target(bpm: int | float | None) -> int:
    if bpm is None:
        return UINT32_INVALID

    # Bryton Active visualizza i target HR come valore_FIT - 100.
    # Esempio: se scriviamo 165, l'app mostra 65 bpm.
    # Quindi salviamo bpm + 100.
    return int(round(float(bpm))) + 100


def _step_name(index: int, total: int, step: dict[str, Any]) -> str:
    if index == 0:
        return "Riscaldamento"
    if index == total - 1:
        return "Raffreddamento"

    target_type = str(step.get("target_type") or "")

    low = int(step.get("target_low") or 0)
    high = int(step.get("target_high") or 0)

    if target_type == "heart_rate":
        # FC: zona alta = lavoro, zona media/bassa = recupero.
        if high >= 160:
            return "Attività"
        return "Recupero"

    if high >= 250:
        return "Attività"
    return "Recupero"


def _intensity(index: int, total: int, step: dict[str, Any]) -> int:
    # FIT intensity enum:
    # 0=active, 1=rest, 2=warmup, 3=cooldown
    if index == 0:
        return 2
    if index == total - 1:
        return 3

    target_type = str(step.get("target_type") or "")
    high = int(step.get("target_high") or 0)

    if target_type == "heart_rate":
        if high >= 160:
            return 0
        return 1

    if high >= 250:
        return 0
    return 1


def _target_values(step: dict[str, Any], ftp: int | float | None) -> tuple[int, int, int]:
    """
    Ritorna:
        fit_target_type, custom_low, custom_high

    Power Bryton:
        target_type = 245
        custom values = 100000 + %FTP

    Heart rate:
        target_type = 1
        custom values = bpm diretti
    """
    target_type = str(step.get("target_type") or "")

    low = step.get("target_low")
    high = step.get("target_high")

    if target_type == "heart_rate":
        return 1, _hr_to_target(low), _hr_to_target(high)

    if target_type == "power":
        return (
            245,
            _watts_to_bryton_ftp_target(low, ftp),
            _watts_to_bryton_ftp_target(high, ftp),
        )

    return UINT8_INVALID, UINT32_INVALID, UINT32_INVALID


def build_minimal_workout_fit(info: dict[str, Any], output_path: Path) -> Path:
    """
    Genera un FIT workout compatibile con Bryton Active.

    Supporta:
    - POWER da Intervals: watt assoluti convertiti in %FTP Bryton
    - HR / FC da Intervals: bpm diretti
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    name = str(info.get("name") or "Intervals Workout")[:40]
    intervals = info.get("interval") or []
    total_steps = len(intervals)
    created_ms = int(info.get("create_time") or int(time.time() * 1000))
    ftp = info.get("ftp") or 267

    records = bytearray()

    records += _def_message(
        0,
        0,
        [
            (0, 1, 0x00),
            (1, 2, 0x84),
            (2, 2, 0x84),
            (3, 4, 0x86),
            (4, 4, 0x86),
        ],
    )
    records += _data_message(
        0,
        b"".join(
            [
                _u8(5),
                _u16(255),
                _u16(0),
                _u32(0x4253594E),
                _u32(_fit_time_ms(created_ms)),
            ]
        ),
    )

    records += _def_message(
        1,
        26,
        [
            (4, 1, 0x00),
            (6, 2, 0x84),
            (8, 64, 0x07),
        ],
    )
    records += _data_message(
        1,
        b"".join(
            [
                _u8(2),
                _u16(total_steps),
                _string_field(name, 64),
            ]
        ),
    )

    records += _def_message(
        2,
        27,
        [
            (254, 2, 0x84),
            (0, 32, 0x07),
            (1, 1, 0x00),
            (2, 4, 0x86),
            (3, 1, 0x00),
            (4, 4, 0x86),
            (5, 4, 0x86),
            (6, 4, 0x86),
            (7, 1, 0x00),
        ],
    )

    for idx, step in enumerate(intervals):
        duration_type = str(step.get("duration_type") or "")

        if duration_type == "repeat_until_steps_cmplt":
            payload = b"".join(
                [
                    _u16(idx),
                    _string_field("", 32),
                    _u8(6),
                    _u32(int(step.get("duration_step") or 0)),
                    _u8(UINT8_INVALID),
                    _u32(int(step.get("repeat_steps") or 1)),
                    _u32(UINT32_INVALID),
                    _u32(UINT32_INVALID),
                    _u8(UINT8_INVALID),
                ]
            )
        else:
            duration_seconds = int(step.get("duration_value") or 1)
            fit_target_type, low_target, high_target = _target_values(step, ftp)

            payload = b"".join(
                [
                    _u16(idx),
                    _string_field(_step_name(idx, total_steps, step), 32),
                    _u8(0),
                    _u32(max(1, duration_seconds) * 1000),
                    _u8(fit_target_type),
                    _u32(0),
                    _u32(low_target),
                    _u32(high_target),
                    _u8(_intensity(idx, total_steps, step)),
                ]
            )

        records += _data_message(2, payload)

    header_size = 14
    protocol_version = 0x10
    profile_version = 0x0864
    data_size = len(records)

    header_without_crc = struct.pack(
        "<BBHI4s",
        header_size,
        protocol_version,
        profile_version,
        data_size,
        b".FIT",
    )
    header_crc = _crc16(header_without_crc)
    header = header_without_crc + struct.pack("<H", header_crc)

    file_without_crc = header + records
    file_crc = _crc16(file_without_crc)

    output_path.write_bytes(file_without_crc + struct.pack("<H", file_crc))

    output_path.with_suffix(".json").write_text(
        json.dumps(info, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return output_path