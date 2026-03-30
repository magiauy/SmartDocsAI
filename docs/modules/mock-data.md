# Mock Data Module

## Purpose

`mock_data` provides simple seed helpers for local development and quick demos.

It is not part of the live API surface, but it makes it easier to pre-create sample rows when testing flows manually.

## Main File

- `backend/apps/mock_data/seeders.py`

## Current Helpers

- `build_sample_documents()`
  - creates a minimal indexed sample document
- `build_sample_conversation()`
  - creates a ready conversation with one assistant bootstrap message

## Dependencies

- depends on `documents`
- depends on `chat`

## What To Extend Next

- add management commands for loading sample data
- create multi-document seed scenarios
- add sample messages that mimic real retrieval-backed responses
