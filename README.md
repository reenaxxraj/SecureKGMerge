<div id="top"></div>
<!-- PROJECT LOGO align="center" -->
![image](https://user-images.githubusercontent.com/44928185/159170631-196b1288-ed73-4811-95a4-1a70d8cbc618.png)

# SecureKGMerge

By Reenashini Rajendran 
as part of Final Year Project on Privacy Preserving KG Merging

<!-- Overview -->
## Overview
SecureKGMerge is an system designed to use PSI to merge multiple isolated KGs to (1) generate meaningful insights for the organisation while (2) protecting the privacy of the disparate data sources. 
This application was applied to a simulated banking setting with 3 isolated departments incharge of one financial product (1. Credit Card, 2. Remittance, 3. Local Bank Transfers). SecureKGMerge transforms the underlying data of each department into Knowledge Graphs
and then performs PSI between any two KGs. Using this technique, we attempt to detect the presence of a loop which indicates the possibility of money laundering among the transactions of the isolated department.  

<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running follow these simple example steps.

### Prerequisites

This is an example of how to list things you need to use the software and how to install them.
* Python3
  ```sh
  Install from https://docs.docker.com/desktop/windows/install/
  ```
* Visual Studio
  ```sh
  Install from https://docs.microsoft.com/en-us/dotnet/framework/install/guide-for-developers
  ```
 * Neo4j Desktop
  ```sh
  Install from https://docs.microsoft.com/en-us/dotnet/framework/install/guide-for-developers
  ```
 * Postman
  ```sh
  Install from https://docs.microsoft.com/en-us/dotnet/framework/install/guide-for-developers
  ``` 

### Installation

1. Clone the repo
   ```sh
   git clone 
   ```
2. Start the server application
   ```sh
   cd CZ4010AppliedCryptoProject/CZ4010-Server
   docker-compose build
   docker-compose up
   ```
3. Start the client application in either Visual Studio or Jetbrains Rider.

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- SECURITY GUARANTEES -->
## Security Guarantees

We would like to provide a brief analysis of the security guarantees each of the core functionalities provide.

- **UploadFile**
    - Honest Conditions (Guarantee "Liveness")
        - Successful upload of encrypted file
        - Encrypted file is also signed to prove ownership
    - Malicious Conditions (Guarantee "Safety")
        - File may not be stored on the server, but is guaranteed to stay encrypted regardless
        - Server has no access to symmetric key needed to decrypt
- **DownloadFile**
    - Honest Conditions (Guarantee "Liveness")
        - Successful download of encrypted file and key
        - Encrypted file can be decrypted
        - Unauthorised users cannot download the file, nor do they have a key
    - Malicious Conditions (Guarantee "Safety")
        - Unauthorised users may download the file, but have no key to decrypt it
        - Server may deny the file to authorised users
- **ModifyFile**
    - Honest Conditions (Guarantee "Liveness")
        - Old file will be replaced by new file
        - Both are encrypted, people who could access the old one can access the new one
        - Only file owner can modify
    - Malicious Conditions (Guarantee "Safety")
        - Old file may not be replaced
        - New file may not be uploaded
        - Files remain encrypted
        - Other users may "modify" even though they are not the file owner, but signature verification of the encrypted file will fail.
- **ShareFile**
    - Honest Conditions (Guarantee "Liveness")
        - File will successfully be shared with users specified
    - Malicious Conditions (Guarantee "Safety")
        - File may not be shared with specified users
        - Regardless, file will not be able to be decrypted by unspecified users
- **UnshareFile**
    - Honest Conditions (Guarantee "Liveness")
        - File will be denied to users specified
        - Specified users' keys will be deleted
    - Malicious Conditions (No Guarantee)
        - Server may refuse to delete specified users' keys allowing them to continue accessing the file.
- **DeleteFile**
    - Honest Conditions (Guarantee "Liveness")
        - File will be deleted
        - All keys will also be deleted
    - Malicious Conditions (No Guarantee)
        - File may not be deleted
        - Users may still be able to access file
- **Logging**
    - Honest Conditions (Guarantee "Liveness")
        - Logs accurately reflect the actions of users
    - Malicious Conditions (Partially Guarantee "Safety")
        - Logs may be deleted by the server even though the user made the request
        - Any log that does exist is guaranteed to be real as server cannot forge user signatures on the request

<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#top">back to top</a>)</p>

