# **🚧 This is a work in progress not yet released for usage**


# **Helm Values Manager 🚀**
🔐 **Secure & Manage Helm Configurations and Secrets Easily!**

Helm Values Manager is a **Helm plugin** designed to simplify **configuration and secret management** across multiple **Kubernetes deployments**. It provides an intuitive **CLI** to define, validate, and securely store configuration values for Helm-based applications.

---

## **✨ Features**
- 🔴 **Deployment-Aware Configuration Management** – Define **global and per-environment configurations**.
- 🔴 **Secure Secret Storage** – Integrates with
    - 🔴 **Google Secret Manager**
    - 🔴 **AWS Secrets Manager**
    - 🔴 **Azure Key Vault**
    - 🔴 **HashiCorp Vault**
    - 🔴 **Git-Secrets**
    - 🔧 **Easily Extendable** – Implement your own backend using the **SecretManager API**.
- 🔴 **Autocompletion Support** – Smooth CLI experience with **Typer-based interactive commands**.
- 🔴 **Validation & Missing Keys Detection** – Avoid misconfigurations with **automated checks**.
- 🔴 **Extensible Secret Manager** – Easily add new **custom backends** for secret storage.
- 🔴 **Seamless ArgoCD & Helm Integration** – Works **out-of-the-box** with Helm-based GitOps workflows.

---

## **🚀 Quick Start**
1️⃣ **Install the Helm Plugin**
```sh
helm plugin install https://github.com/your-org/helm-values-manager.git
```

2️⃣ **Initialize a New Configuration**
```sh
helm values-manager init my-release
```

3️⃣ **Define a Deployment & Add Keys**
```sh
helm values-manager add-deployment dev --secrets-backend=aws_secrets_manager
helm values-manager add-key DATABASE_URL --required --sensitive --path=global.database.url
```

4️⃣ **Set & Retrieve Secret Values**
```sh
helm values-manager add-secret DATABASE_URL=mydb://connection --deployment=dev
helm values-manager get-secret DATABASE_URL --deployment=dev
```

5️⃣ **Validate Configurations**
```sh
helm values-manager validate
```

6️⃣ **Generate the Final `values.yaml`**
```sh
helm values-manager generate --deployment=dev
```

---

## **📜 Documentation**
📖 **[Read the Full Documentation](https://github.com/your-org/helm-values-manager/wiki)**
💡 **[View the Architecture Decision Record (ADR)](https://github.com/your-org/helm-values-manager/wiki/ADRs/001-helm-values-manager.md)**
🛠 **[Contribute to the Project](https://github.com/your-org/helm-values-manager/wiki/Contribution/contributing.md)**

---

## **🤝 Contributing**
Want to help? Check out our **[contribution guidelines](https://github.com/your-org/helm-values-manager/wiki/Contribution/contributing.md)**! We welcome issues, PRs, and feature suggestions. 🎉

---

## **📌 License**
🔓 Open-source under the **MIT License**.

---

### **🌟 Star this repo if you find it useful! 🌟**
🙌 PRs and contributions are welcome! Let's build a better **Helm secret & config manager** together. 🚀
