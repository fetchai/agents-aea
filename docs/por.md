
An AEA can use several key pairs. In particular, it can use different keys for securing its communication and for engaging in exchange. In the ACN we make use of this fact. To be able to signal to other agents that the address derived from one key pair is allowed to represent the agent controlling the other key pair, the key pair which is being represented must sign a message to prove that the other key pair is allowed to represent it. The `aea issue-certificates` command allows to create this association.

The proof of representation feature is used in the context of the `fetchai/p2p_libp2p` and `fetchai/p2p_libp2p_client` connection.

In the former connection, the configuration YAML specifies a `cert_requests` field:

``` yaml
cert_requests:
- identifier: acn
  ledger_id: fetchai
  not_after: '2022-01-01'
  not_before: '2021-01-01'
  public_key: fetchai
  message_format: '{public_key}'
  save_path: .certs/conn_cert.txt
```

The `identifier` refers to the environment for which the signature is generated, here `acn`. The `ledger_id` refers to the key pair to be used from the `private_key_paths` specified in `aea-config.yaml` for signing. The `not_after` and `not_before` fields specify constraints on the validity of the signature. The `public_key` can specify either the identifier of the key pair in `connection_private_key_paths` of which the public key is signed or it can contain the to be signed public key in plain text. The `save_path` specifies the path where the certificate is to be saved at.

In the above example, the connection requests a certificate which is a signature of the `fetchai` public key in `connection_private_key_paths` with the `fetchai` key pair in `private_key_paths`. The validity of the signature will be constrained to the year `2021` for the environment `acn`.
