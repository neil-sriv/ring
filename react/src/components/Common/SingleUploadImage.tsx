import {
  Box,
  Center,
  chakra,
  Icon,
  IconButton,
  Image,
  Input,
  ScaleFade,
  VStack,
} from "@chakra-ui/react";
import { useState } from "react";
import { FaTimes } from "react-icons/fa";
import { MdAddPhotoAlternate } from "react-icons/md";

/**
 * SingleUploadImage Component
 *
 * This component provides a user-friendly interface for uploading a single image.
 * It includes an option to preview the selected image and supports customization for size and rounding.
 *
 * @component
 *
 * @props {string} [size='100px'] - Specifies the dimensions of the upload area.
 * @props {string} [rounded='full'] - Defines the border-radius for the upload area, creating rounded corners.
 * @props {function} onUpdateFile (Required) - A callback function invoked when a new image is selected.
 *                                              It receives the selected image file as a parameter.
 *
 * @example
 * // Usage Example
 * <SingleUploadImage
 *   size="150px"
 *   rounded="md"
 *   onUpdateFile={handleFileUpdate}
 * />
 *
 * @example
 * // Import Example
 * import { SingleUploadImage } from './path-to-components';
 *
 * const YourComponent = () => {
 *   const handleFileUpdate = (file) => {
 *     // Handle the selected file (e.g., upload to server, update state)
 *     console.log('Selected File:', file);
 *   };
 *
 *   return (
 *     <SingleUploadImage
 *       size="150px"
 *       rounded="md"
 *       onUpdateFile={handleFileUpdate}
 *     />
 *   );
 * };
 */
type SingleUploadImageProps = {
  size?: string;
  onUpdateFile(file: File): Promise<void>;
  name: string;
};

export function SingleUploadImage({
  size = "50px",
  onUpdateFile,
  name,
}: SingleUploadImageProps): JSX.Element {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { files } = event.target;
    if (!files || files.length === 0) {
      return;
    }
    const selectedFiles = files as FileList;
    const file = selectedFiles?.[0];
    setUploadedFile(file);
    await onUpdateFile(file);
    setUploadedFile(null);
  };

  return (
    <Center
      w={size}
      h={size}
      as={chakra.label}
      htmlFor={name}
      cursor="pointer"
      overflow="hidden"
      position="relative"
    >
      <Center
        position="absolute"
        w="100%"
        h="100%"
        _hover={{ bg: "blackAlpha.600" }}
      >
        <VStack>
          {uploadedFile == null && <Icon as={MdAddPhotoAlternate} />}
        </VStack>
      </Center>

      {uploadedFile && (
        <ScaleFade initialScale={0.9} in={uploadedFile !== null}>
          <Image
            w="100%"
            h={"100%"}
            src={URL.createObjectURL(uploadedFile)}
            alt="Uploaded"
          />
        </ScaleFade>
      )}

      <Input
        required
        style={{ display: "none" }}
        type="file"
        // id="file"
        // name="file"
        id={name}
        name={name}
        onChange={handleFileChange}
        isDisabled={uploadedFile !== null}
        accept="image/*, video/*"
      />
    </Center>
  );
}

interface S3MediaProps {
  s3Key: string;
  alt?: string;
  handleDelete?: () => void;
}

function S3MediaContainer({ children }: { children: React.ReactNode }) {
  return (
    <Box
      borderRadius="md"
      _hover={{
        boxShadow: "md",
        transition: "all 0.2s ease-in-out",
      }}
      transition="all 0.2s ease-in-out"
      boxShadow="sm"
      overflow="hidden"
      display="inline-block"
      p={2}
      position="relative"
    >
      {children}
    </Box>
  );
}

export function S3Image({ s3Key, alt, handleDelete }: S3MediaProps) {
  const url = `https://du32exnxihxuf.cloudfront.net/${s3Key}`;
  return (
    <S3MediaContainer>
      <Image
        src={url}
        alt={alt}
        maxW="400px"
        maxH="300px"
        objectFit="contain"
        _hover={{
          transform: "scale(1.02)",
          transition: "all 0.2s ease-in-out",
        }}
        transition="all 0.2s ease-in-out"
      />
      {handleDelete && <IconButton
        aria-label="Delete image"
        icon={<FaTimes />}
        size="sm"
        colorScheme="red"
        variant="solid"
        position="absolute"
        top={3}
        right={3}
        opacity={0.7}
        _hover={{ opacity: 1 }}
        onClick={handleDelete}
        zIndex={1}
      />}
    </S3MediaContainer>
  );
}

export function S3Video({ s3Key, handleDelete }: { s3Key: string; handleDelete?: () => void }) {
  const url = `https://du32exnxihxuf.cloudfront.net/${s3Key}`;
  return (
    <S3MediaContainer>
      <Box
        as="video"
        src={url}
        controls
        maxW="400px"
        maxH="300px"
        objectFit="contain"
      />
      {handleDelete && <IconButton
        aria-label="Delete video"
        icon={<FaTimes />}
        size="sm"
        colorScheme="red"
        variant="solid"
        position="absolute"
        top={3}
        right={3}
        opacity={0.7}
        _hover={{ opacity: 1 }}
        onClick={handleDelete}
        zIndex={1}
      />}
    </S3MediaContainer>
  );
}
