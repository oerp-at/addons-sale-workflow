import {KanbanRecord} from "@web/views/kanban/kanban_record";
import {patch} from "@web/core/utils/patch";

// Project sharing: a task whose stage and status are driven by its counterpart
// (state_change_permission false) cannot be dragged into another stage or status
// column. The server refuses the move, and portal users never see server errors
// (core handler "swallowAllVisitorErrors"), so the card would just jump back.
const LOCKED_GROUP_BYS = ["stage_id", "state"];

patch(KanbanRecord.prototype, {
    getCardClasses() {
        const classes = super.getCardClasses();
        const {record, groupByField} = this.props;
        if (
            record.resModel === "project.task" &&
            LOCKED_GROUP_BYS.includes(groupByField?.name) &&
            record.data.state_change_permission === false
        ) {
            return classes
                .split(" ")
                .filter((cls) => cls !== "o_draggable")
                .join(" ");
        }
        return classes;
    },
});
