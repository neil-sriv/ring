import {
  Box,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerOverlay,
  Flex,
  Heading,
  IconButton,
  Text,
  useColorModeValue,
  useDisclosure,
} from "@chakra-ui/react";
import { useQueryClient } from "@tanstack/react-query";
import { FiLogOut, FiMenu } from "react-icons/fi";

import { Link } from "@tanstack/react-router";
import type { UserLinked } from "../../client";
import { readUserMePartiesMeGetQueryKey } from "../../client/@tanstack/react-query.gen";
import useAuth from "../../hooks/useAuth";
import SidebarItems from "./SidebarItems";

const Sidebar = () => {
  const queryClient = useQueryClient();
  const textColor = useColorModeValue("ui.dark", "ui.light");
  const currentUser = queryClient.getQueryData<UserLinked>(
    readUserMePartiesMeGetQueryKey()
  );
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { logout } = useAuth();

  const handleLogout = async () => {
    logout();
    queryClient.clear();
  };

  return (
    <>
      {/* Mobile */}
      <IconButton
        onClick={onOpen}
        display={{ base: "flex", md: "none" }}
        aria-label="Open Menu"
        position="fixed"
        top={4}
        left={4}
        fontSize="20px"
        icon={<FiMenu />}
        bg="ui.glass.light.background"
        color="ui.dark"
        backdropFilter="blur(10px)"
        border="1px solid"
        borderColor="ui.glass.light.border"
        _hover={{ bg: "ui.glass.light.background", opacity: 0.9 }}
        _dark={{
          bg: "ui.glass.dark.background",
          color: "ui.light",
          borderColor: "ui.glass.dark.border",
        }}
        zIndex={1000}
      />
      <Drawer isOpen={isOpen} placement="left" onClose={onClose}>
        <DrawerOverlay backdropFilter="blur(4px)" />
        <DrawerContent 
          maxW="240px" 
          bg="ui.glass.light.background"
          backdropFilter="blur(10px)"
          border="1px solid"
          borderColor="ui.glass.light.border"
          _dark={{
            bg: "ui.glass.dark.background",
            borderColor: "ui.glass.dark.border",
          }}
        >
          <DrawerCloseButton color={textColor} />
          <DrawerBody py={8}>
            <Flex flexDir="column" justify="space-between" h="100%">
              <Box>
                <Heading 
                  size="lg" 
                  textAlign="center" 
                  p={4}
                  color={textColor}
                  fontWeight="bold"
                  letterSpacing="tight"
                >
                  <Link to="/">Ring</Link>
                </Heading>
                <SidebarItems onClose={onClose} />
                <Flex
                  as="button"
                  onClick={handleLogout}
                  p={3}
                  mt={4}
                  color="ui.danger"
                  fontWeight="bold"
                  alignItems="center"
                  borderRadius="md"
                  _hover={{ bg: "ui.danger", color: "white" }}
                  transition="all 0.2s"
                >
                  <FiLogOut />
                  <Text ml={2}>Log out</Text>
                </Flex>
              </Box>
              {currentUser?.email && (
                <Text 
                  color={textColor} 
                  noOfLines={2} 
                  fontSize="sm" 
                  p={4}
                  borderTop="1px solid"
                  borderColor="ui.glass.light.border"
                  _dark={{
                    borderColor: "ui.glass.dark.border"
                  }}
                >
                  Logged in as: {currentUser.email}
                </Text>
              )}
            </Flex>
          </DrawerBody>
        </DrawerContent>
      </Drawer>

      {/* Desktop */}
      <Box
        position="sticky"
        top={0}
        h="100vh"
        display={{ base: "none", md: "flex" }}
        zIndex={1}
        p={4}
      >
        <Flex
          flexDir="column"
          justify="space-between"
          bg="ui.glass.light.background"
          backdropFilter="blur(10px)"
          border="1px solid"
          borderColor="ui.glass.light.border"
          _dark={{
            bg: "ui.glass.dark.background",
            borderColor: "ui.glass.dark.border",
          }}
          p={6}
          w="240px"
          boxShadow="xl"
          borderRadius="xl"
        >
          <Box>
            <Heading 
              size="lg" 
              textAlign="center" 
              p={4}
              color={textColor}
              fontWeight="bold"
              letterSpacing="tight"
            >
              <Link to="/">Ring</Link>
            </Heading>
            <SidebarItems />
            <Flex
              as="button"
              onClick={handleLogout}
              p={3}
              mt={4}
              color="ui.danger"
              fontWeight="bold"
              alignItems="center"
              borderRadius="md"
              _hover={{ bg: "ui.danger", color: "white" }}
              transition="all 0.2s"
            >
              <FiLogOut />
              <Text ml={2}>Log out</Text>
            </Flex>
          </Box>
          {currentUser?.email && (
            <Text 
              color={textColor} 
              noOfLines={2} 
              fontSize="sm" 
              p={4}
              borderTop="1px solid"
              borderColor="ui.glass.light.border"
              _dark={{
                borderColor: "ui.glass.dark.border"
              }}
            >
              Logged in as: {currentUser.email}
            </Text>
          )}
        </Flex>
      </Box>
    </>
  );
};

export default Sidebar;
