<!-- PROJECT LOGO align -->
![image](https://user-images.githubusercontent.com/44928185/159171729-6cb1f9f1-478c-43cc-ba8d-f9cd5711bfa0.png)

<div id="top"></div>

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

* Python3
* Visual Studio
* Neo4j Desktop
* Postman
* OpenMined PSI
```sh
pip install openmined_psi
``` 
* Flask
```sh
pip install flask
``` 
* Protobuf
```sh
pip install google.protobuf
``` 
* Colorama
```sh
pip install colorama
``` 

### Deployment

1. Clone the repo
   ```sh
   git clone https://github.com/reenaxxraj/SecureKGMerge.git
   ```
2. Load KGs into Neo4j desktop and deploy graph database
   ```sh

   ```
3. Run python files.
4. Query 

<p align="right">(<a href="#top">back to top</a>)</p>




<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#top">back to top</a>)</p>

