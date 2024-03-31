export async function authenticate(
  prevState: void | undefined,
  formData: FormData
) {
  try {
    const data = {
      username: formData.get("email"),
      password: formData.get("password"),
    };
    console.log(data);
    const res = await fetch("/api/token", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        accept: "application/json",
      },
      body: new URLSearchParams(data),
    }).catch((error) => {
      console.error("Error:", error);
      throw new Error("Something went wrong.");
    });
    console.log(await res.json());
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
