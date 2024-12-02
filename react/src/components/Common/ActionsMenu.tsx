import {
  Button,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  useDisclosure,
} from "@chakra-ui/react";
import { BsThreeDotsVertical } from "react-icons/bs";
import { FiEdit, FiSettings, FiTrash } from "react-icons/fi";

import type { GroupLinked, UserLinked } from "../../client";
import EditUser from "../Admin/EditUser";
import Delete from "./DeleteAlert";
import EditGroup from "../Groups/EditGroup";
import AddMembers from "../Groups/AddMembers";
import { useNavigate } from "@tanstack/react-router";

interface ActionsMenuProps {
  type: string;
  value: GroupLinked | UserLinked;
  disabled?: boolean;
}

const ActionsMenu = ({ type, value, disabled }: ActionsMenuProps) => {
  const editUserModal = useDisclosure();
  const deleteModal = useDisclosure();
  const addMembersModal = useDisclosure();
  const navigate = useNavigate();

  return (
    <>
      <Menu>
        <MenuButton
          isDisabled={disabled}
          as={Button}
          rightIcon={<BsThreeDotsVertical />}
          variant="unstyled"
        />
        <MenuList>
          <MenuItem
            onClick={editUserModal.onOpen}
            icon={<FiEdit fontSize="16px" />}
          >
            Edit {type}
          </MenuItem>
          <MenuItem
            onClick={deleteModal.onOpen}
            icon={<FiTrash fontSize="16px" />}
            color="ui.danger"
          >
            Delete {type}
          </MenuItem>
          {type === "Group" && (
            <>
              <MenuItem
                icon={<FiEdit fontSize="16px" />}
                onClick={addMembersModal.onOpen}
              >
                Add Members
              </MenuItem>
              <MenuItem
                icon={<FiSettings fontSize="16px" />}
                onClick={() =>
                  navigate({
                    to: "/groups/$groupId/settings",
                    params: { groupId: value.api_identifier },
                  })
                }
              >
                Settings
              </MenuItem>
            </>
          )}
        </MenuList>
        {type === "User" ? (
          <EditUser
            user={value as UserLinked}
            isOpen={editUserModal.isOpen}
            onClose={editUserModal.onClose}
          />
        ) : (
          <>
            <EditGroup
              group={value as GroupLinked}
              isOpen={editUserModal.isOpen}
              onClose={editUserModal.onClose}
            />
            <AddMembers
              group={value as GroupLinked}
              isOpen={addMembersModal.isOpen}
              onClose={addMembersModal.onClose}
            />
          </>
        )}
        <Delete
          type={type}
          id={value.api_identifier}
          isOpen={deleteModal.isOpen}
          onClose={deleteModal.onClose}
        />
      </Menu>
    </>
  );
};

export default ActionsMenu;
