export async function authenticate(
  prevState: void | undefined,
  formData: FormData
) {
  try {
    const res = await fetch("/internal/");
    console.log(res);
  } catch (error) {
    // if (error instanceof AuthError) {
    //   switch (error.type) {
    //     case "CredentialsSignin":
    //       return "Invalid credentials.";
    //     default:
    //       return "Something went wrong.";
    //   }
    // }
    throw error;
  }
}
