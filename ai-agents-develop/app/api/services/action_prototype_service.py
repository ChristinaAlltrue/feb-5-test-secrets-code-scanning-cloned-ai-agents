#  Copyright 2023-2024 AllTrue.ai Inc
#  All Rights Reserved.
#
#  NOTICE: All information contained herein is, and remains
#  the property of AllTrue.ai Incorporated. The intellectual and technical
#  concepts contained herein are proprietary to AllTrue.ai Incorporated
#  and may be covered by U.S. and Foreign Patents,
#  patents in process, and are protected by trade secret or copyright law.
#  Dissemination of this information or reproduction of this material
#  is strictly forbidden unless prior written permission is obtained
#  from AllTrue.ai Incorporated.

from alltrue.agents.schema.action_prototype import ActionPrototype

from app.core.registry import PROTOTYPE_REGISTRY


def get_all_action_prototypes() -> list[ActionPrototype]:
    """Retrieve all ActionPrototype records from the database."""
    return [i.prototype for i in PROTOTYPE_REGISTRY.values()]
