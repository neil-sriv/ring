import { Button, Flex, Icon, useDisclosure } from "@chakra-ui/react";
import { FaPlus } from "react-icons/fa";

import AddUser from "../Admin/AddUser";
import AddGroup from "../Groups/AddGroup";

interface NavbarProps {
  type: string;
}

const Navbar = ({ type }: NavbarProps) => {
  const addUserModal = useDisclosure();
  const addGroupModal = useDisclosure();

  const onClick = (type: string): void => {
    if (type === "User") {
      addUserModal.onOpen();
    } else if (type === "Group") {
      addGroupModal.onOpen();
    }
  };
  return (
    <>
      <Flex py={8} gap={4}>
        {/* TODO: Complete search functionality */}
        {/* <InputGroup w={{ base: '100%', md: 'auto' }}>
                    <InputLeftElement pointerEvents='none'>
                        <Icon as={FaSearch} color='ui.dim' />
                    </InputLeftElement>
                    <Input type='text' placeholder='Search' fontSize={{ base: 'sm', md: 'inherit' }} borderRadius='8px' />
                </InputGroup> */}
        <Button
          variant="primary"
          gap={1}
          fontSize={{ base: "sm", md: "inherit" }}
          onClick={() => onClick(type)}
        >
          <Icon as={FaPlus} /> Add {type}
        </Button>
        <AddUser isOpen={addUserModal.isOpen} onClose={addUserModal.onClose} />
        <AddGroup
          isOpen={addGroupModal.isOpen}
          onClose={addGroupModal.onClose}
        />
      </Flex>
    </>
  );
};

export default Navbar;
