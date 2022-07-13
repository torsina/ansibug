# -*- coding: utf-8 -*-
# Copyright (c) 2022 Jordan Borean
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
name: debug
short_description: Executes tasks with a Debug Adapter Protocol debugger
description:
- Acts like the linear strategy plugin but adds functionality for interacting
  with a Debug Adapter Protocol (DAP) debugger, like one used by
  Visual Studio Code.
author: Jordan Borean (@jborean93)
"""

import enum
import typing as t

from ansible import constants as C
from ansible.errors import AnsibleAssertionError, AnsibleError, AnsibleParserError
from ansible.executor.play_iterator import (
    FailedStates,
    HostState,
    IteratingStates,
    PlayIterator,
)
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory.host import Host
from ansible.inventory.manager import InventoryManager
from ansible.module_utils._text import to_text
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.block import Block
from ansible.playbook.included_file import IncludedFile
from ansible.playbook.play import Play
from ansible.playbook.play_context import PlayContext
from ansible.playbook.task import Task
from ansible.plugins.loader import action_loader
from ansible.plugins.strategy import StrategyBase
from ansible.plugins.strategy.linear import StrategyModule as LinearStrategy
from ansible.template import Templar
from ansible.utils.display import Display
from ansible.vars.manager import VariableManager

import ansibug

display = Display()


class DebugState(ansibug.DebugState):
    def __init__(self) -> None:
        self._counters = {
            "thread": 1,
        }
        self._threads: t.Dict[int, ansibug.dap.Thread] = {}

    def add_thread(
        self,
        name: str,
    ) -> int:
        tid = self._counters["thread"]
        self._counters["thread"] += 1
        self._threads[tid] = ansibug.dap.Thread(id=tid, name=name)

        return tid

    def get_threads(
        self,
        request: ansibug.dap.ThreadsRequest,
    ) -> t.Iterable[ansibug.dap.Thread]:
        return self._threads.values()


class StrategyModule(LinearStrategy):
    def __init__(
        self,
        tqm: TaskQueueManager,
    ) -> None:
        super().__init__(tqm)

    def _set_hosts_cache(
        self,
        play: Play,
        refresh: bool = True,
    ) -> None:
        """If refresh=True this should update the task list with self.get_hosts_left(None)"""
        return super()._set_hosts_cache(play, refresh)

    def _execute_meta(
        self,
        task: Task,
        play_context: PlayContext,
        iterator: PlayIterator,
        target_host: Host,
    ) -> t.List[t.Dict[str, t.Any]]:
        """Called when a meta task is about to run"""
        return super()._execute_meta(task, play_context, iterator, target_host)

    def _queue_task(
        self,
        host: Host,
        task: Task,
        task_vars: t.Dict[str, t.Any],
        play_context: PlayContext,
    ) -> None:
        """Called just as a task is about to be queue"""
        return super()._queue_task(host, task, task_vars, play_context)

    def run(
        self,
        iterator: PlayIterator,
        play_context: PlayContext,
    ) -> int:
        """Can build the host/thread list here"""
        return super().run(iterator, play_context)


# Other things to look at
#   * Need some way for something to hook in and validate breakpoints being requested
#   * IncludeFile.process_include_results (called after queue_task) to process
#       any queue entries and check breakpoints?
#   * Get details when a task finishes (_process_pending_results or _wait_pending_results)?
#   * Deal with handlers - _do_handler_run
#   * Should we have an uncaught exception (not rescue on failed task)
#   * Should we have a raised exception (- fail:) task
