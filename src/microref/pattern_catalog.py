patterns = {
    "Application Package":
        """
        Application Package

        You are implementing an application with a Cloud-Native

        Architecture . You have a choice of computer languages to use to
        implement the application and want to choose one that will work well in
        the cloud.

        What features of a computer language ecosystem are required to implement
        a Cloud Application?

        The cloud is very flexible and able to run pretty much any program
        implemented in any language that can run in a standard operating
        system, such as Linux or Windows. Yet for a program to run well in the
        cloud, some conventions must be followed to remove dependencies the
        cloud may not be able to provide.

        Traditional IT applications tend to be highly dependent on their
        hardware and operating system. A program written in a language like
        Assembler or C would run correctly only on a certain hardware model
        running a specific operating system version, and even then it would
        often require installing optional features and otherwise configuring
        the OS in a very specific way. Before the application could be
        installed, the operating system had to be customized for the
        application. The program might even be dependent on a specific version
        of the operating system. When a new version of the OS was released,
        some programs that worked in the old version wouldn’t work in the new
        one. Programs needed complicated installers to verify all of these
        dependencies and perform the necessary configuration.

        Programs can not only be dependent on a specific operating system with
        optional features and a specific configuration; they can often have
        other dependencies as well. Programs often require additional
        libraries, and each program requires different libraries. At best,
        these libraries have to be installed on the OS as part of installing
        the program. A way to avoid this complexity is to have the program
        dynamically load the required libraries from elsewhere. At startup, the
        program downloads the libraries from a central catalog. This creates a
        major dependency on the catalog that can cause problems for starting
        the program. If the program cannot access the catalog, it cannot run.
        If the catalog doesn’t contain the right libraries or contains the
        wrong versions of the libraries, the program cannot run.

        Traditional IT applications often customize their platform so much that
        two applications cannot be installed on the same platform. One
        application requires an extensive set of configuration settings, and
        another requires its own incompatible settings. Two applications
        delegate to the same library, but require two different versions of the
        library, yet only one can be installed on the platform. Each
        application must be run on a separate computer so that it can uniquely
        customize its computer.

        For a program to run in the cloud, it needs to be portable. It needs to
        be isolated from the OS and able to run on a range of compatible
        versions. It needs to include everything needed to run, with no
        dependencies on outside catalogs or other resources. It needs to be
        able to install on the same computer as other program—none of them can
        customize it.

        Therefore,

        Implement an application’s program in a language and toolset that
        encapsulates the application as an Application Package. Package the
        application with all dependencies that the program requires to run.

        An Application Package contains a program and everything else

        needed to run the program. Figure 3-4 shows an Application Package that
        contains a program and two libraries.



        Figure 3-4. Application Package



        An Application Package is specific to a particular language. It contains
        a program implemented in that language, includes code libraries
        implemented in that same language, and includes configuration settings
        meaningful to that language.

        An Application Package is not a running application, but the cloud
        platform can deploy it as an application.

        As Figure 3-5 shows, the cloud platform’s management functionality
        includes an application deployer, which performs the function of
        creating a new workload instance of an application from its Application
        Package.





        Figure 3-5. Service API

        Modern programming languages such as Java, Node.js, and Go are
        cloud-friendly because they encapsulate a program in an Application
        Package. To build and run a program as an Application Package, the
        language uses two features:

        Runtime environment

        A separately installable, language-specific runtime that executes the
        program. Any program written in this language can reuse the runtime
        environment. The runtime isolates the program from the OS, so that the
        program has no direct dependencies on the OS and the same program can
        run unchanged on multiple OSs. The runtime environment may be a
        different executable for each OS and hardware architecture.

        Package manager

        An application that packages the program with all of the libraries,
        dependencies, and configuration that the program specifies. This
        packaged program will run in the runtime environment on any operating
        system. The package manager needs access to a registry of libraries to
        build the package, but the runtime environment does not need access to
        the library registry because the package

        contains the libraries. The package manager may be part of the runtime
        environment or may be separate.

        An Application Package runs in its runtime environment, which

        runs in the operating system. Figure 3-6 shows that stack for running
        the program.





        Figure 3-6. Running program

        Programs that run in a runtime environment are more portable because
        they can run anywhere the runtime environment is installed. Java was
        one of the first programming languages to introduce a runtime
        environment. The Java Runtime Environment (JRE) that incorporates the
        Java Virtual Machine (JVM) provides a standard set of functionality for
        running a program. Different implementations of the JVM run on
        different operating systems, such as Windows, macOS, and Linux. The
        Java slogan was “Write once, run anywhere,” meaning that the same Java
        program can run on any platform that has the JRE installed. Other
        languages such as Node.js and Python adopted this convention of running
        programs in a runtime environment.

        While a runtime environment enables the same program to run on different
        platforms, an Application Package makes deploying the program in a
        runtime environment simple and reliable. The runtime environment is
        standard, and every Application Package runs in equivalent runtime
        environments. The package is immutable; once it is built, it can be
        deployed repeatedly without changes.

        The program is implemented in a language that can build it as an
        Application Package. A package manager builds the

        Application Package for a program, as shown in Figure 3-7.



        Figure 3-7. Package manager



        The package manager has access to a registry of code libraries for the
        language it packages. The program includes a configuration that lists
        the program’s dependencies, including the code libraries the program
        requires. The package manager packages the program with its libraries
        and other dependencies.

        As explained in The Twelve-Factor App: II. Dependencies:

        A twelve-factor app never relies on implicit existence

        of system-wide packages. It declares all dependencies,

        completely and exactly, via a dependency declaration

        manifest. Furthermore, it uses a dependency isolation tool

        during execution to ensure that no implicit dependencies

        “leak in” from the surrounding system. The full and explicit

        dependency specification is applied uniformly to both

        production and development.

        To deploy an application to run in the cloud, install the runtime
        environment for the application’s programming language onto the cloud
        platform’s OS (usually Linux but possibly Windows), then deploy the
        Application Package into the runtime environment. Once deployed, the
        cloud can start and stop the application as needed.



        An Application Package makes a program simple and reliable to deploy
        anywhere a runtime environment is installed. The package has no
        external dependencies other than the runtime environment. Anywhere the
        cloud can run the runtime environment, it can run the program in its
        Application Package. However, not all programming languages support
        packaging applications and running them in runtime environments.
        Programs written in those languages will be more difficult if not
        impossible to run on the cloud.

        Each Application Package is deployed to its own copy of the runtime
        environment, so each application can be implemented

        in a different language using Polyglot Development .

        Cloud management’s application deployer typically does not actually
        deploy copies of the Application Package but rather

        deploys copies of a virtual machine image or container image that
        includes the Application Package. One advantage of packaging an
        application as an Application Package is that the package makes it
        easier for the cloud platform’s application deployer to deploy the
        application simply and reliably. By packaging the Application Package
        as a virtual machine or container, it is even easier for the
        application deployer to deploy.

        The program in an Application Package to be deployed on the cloud should
        be a Cloud-Native Application, which means it

        exposes its functionality via a Service API , is implemented as a

        Stateless Application that is also a Replicable Application , and

        has an External Configuration . The program uses Backend

        Services , specialized SaaS services that are reusable across
        applications, typically stateful, and often part of the cloud platform
        or otherwise developed by third-party vendors. A typical example is a
        database service hosted in the cloud.

        Examples

        Some examples of popular languages with runtime environments and package
        managers include the following:

        Java

        The runtime environment is the JRE, which includes the JVM. Server
        environments such as Spring Boot, Open Liberty, and Quarkus,
        incorporate the JRE plus additional code libraries. A Java program is
        packaged as a web application archive (WAR or .war ) file or an
        enterprise application archive (EAR or .ear ) file. The Java JDK
        (Java Development Kit), which includes the JRE, doesn’t include a
        built-in package manager, but Maven and Gradle are optional third-party
        package managers for Java.

        JavaScript

        The server runtime environment is Node.js. TypeScript extends Node.js
        with additional code libraries to support type-safe JavaScript. The
        Node Package Manager (NPM)

        packages the program with the libraries specified in the program’s
        configuration and can then run the package.

        Go

        The runtime environment can run a Go source code file on any system
        architecture. It can also build a compiled Go package that runs
        natively in the system architecture used to build it.

        Python, PHP, Ruby, and even COBOL have runtime environments. On the
        other hand, C, C++, Assembler, and shell scripts don’t have separate
        runtimes; those programs are highly dependent on the underlying OS.

        Java

        Java is a particularly interesting example for a package manager because
        the JDK doesn’t include a built-in package manager, but there are two
        commonly used third-party package managers available for Java: Maven
        and Gradle. This separation clearly shows where the language ends and
        the package manager begins; it also shows alternative approaches for
        achieving the same application packaging goal.

        A Java program runs in the JRE, which is part of the JDK for developing
        Java applications, and it is run using the java command. The command
        java runs a program contained in a class file in the JRE, and
        java -jar .jar runs a program contained in a Java Archive (JAR) file.
        The runtime environment contains a catalog of code libraries. When
        running a program, more code libraries can be added to those in the JRE
        by specifying them on the class path. The JRE includes the Java Virtual
        Machine (JVM). There are JVM implementations for Linux, Windows, and
        macOS and even Unix distributions such as Solaris, any of which can run
        any Java program.

        Maven specifies a project’s configuration in the pom.xml file. The
        project specifies the libraries a program requires in the

        dependencies section. Run mvn clean compile to build the

        runtime artifacts. Run mvn package to create a JAR file containing the
        runtime artifacts, which can easily be deployed and run on any computer
        with the JRE installed.

        Gradle specifies a project’s build script in the build.gradle file. The
        project specifies the libraries a program requires in the

        dependencies section, which also specifies how to find those

        libraries in the catalogs specified in the repositories section. The
        items in the plugins section add tasks that assemble the package using
        the dependencies. Run gradlew assemble to run the set of tasks to build
        the runtime artifacts in a JAR file that can run anywhere the JRE is
        installed.

        Open Liberty

        Open Liberty is an application server that implements Java Platform,
        Enterprise Edition (Java EE), and Jakarta EE. A program that runs in
        Open Liberty uses the server.xml file to configure its environment. It
        includes a section to configure the feature manager to load the
        features (which are Java libraries) that the program requires. The
        configured program runs in Java’s JRE.

        For example, the server.xml in Example 3-1 configures the

        server with the library for REST web services (see Service API ).

        Example 3-1. Open Liberty server.xml



        restfulWS-3.0

        ...



        ...



        Then build a server starting with the openliberty-kernel package—which
        is the Liberty server with the minimum set of features possible. The
        build will load only the features specified in the server
        configuration, ensuring that the application has access to the features
        it needs and that the server is as small as possible—only containing
        features that the application requires.

        Node.js

        A Node.js program specifies the libraries it requires as dependencies in
        the package.json file. For example, to specify that the program
        requires the upper-case module,

        include the configuration in Example 3-2.

        Example 3-2. Node.js package.json

        {

        "dependencies": {

        "upper-case": "^2.0.0",

        ...

        },

        ...

        }

        Use NPM to package and run the program. Node is just a runtime
        environment, but NPM is both a package manager and a runtime
        environment that uses Node to run the packages it creates.
        """,
    "Service API":
        """
        Service API

        You are developing an application with a Cloud-Native

        Architecture that runs in an Application Package . You want clients to
        be able to connect to your application in a way that makes both of them
        easier to write and maintain, that supports connecting remotely over a
        network, that performs well over the network, and that supports the
        internet—the universal network.

        How should an application expose its functionality to clients that want
        to use the application?

        An application on a client device invoking behavior in a Cloud
        Application is fundamentally a client/server relationship: the client
        application is invoking behavior on the server. Making client/server
        interactions work well for the cloud entails four levels of
        difficulty:

        Clean separation of client functionality from server

        functionality

        To separate the client from the server, both must be well encapsulated.
        The code in traditional IT applications is often difficult to separate
        into components. Spaghetti code, which is code that depends on any and
        all other code in the application, is difficult to separate into
        parts.

        (See Big Ball of Mud .) What is needed is a wall between the client code
        and the server code that separates the two sets of code, encapsulates
        the server, prevents the server from depending on the client, and
        restricts and controls the dependencies the client has on the server.
        Yet this wall must enable the server to expose its functionality to the
        client so that they can still work together. This wall will enable the
        client and server to evolve independently. It will also enable the two
        development teams working on the client and server to work
        independently, only needing to coordinate on designing the wall between
        the client and server.

        Remote access to the server from the client

        The code in a single application runs in a single process, but a client
        and a server are more useful when they can run in different
        processes—perhaps on different

        computers—connected by a network. However, interprocess communication
        (IPC) is a lot more complicated than one function calling another
        within the

        same process. The fallacies of distributed computing by L. Peter Deutsch
        explain how remote invocation is more complex than it appears. Martin
        Fowler summarized

        them as his First Law of Distributed Object Design: “Don’t distribute
        your objects!” What is so complicated about

        Remote Procedure Invocation (Enterprise Integration

        Patterns, 2003) (aka remote procedure calls (RPCs) and remote method
        invocation (RMI))? First, invocations between processes need a
        synchronous network protocol. To use the protocol, applications need a
        method to serialize complex objects so they can be sent across the
        wire, such as Java or .NET serialization. While there are many
        implementations to choose from, for example, XML-RPC, REST, and gRPC,
        all have disadvantages. This is why there are so many to choose from
        and why new remote protocols are added every few years. To communicate,
        the client and server have to agree on the option they’re going to
        use.

        Efficient communication between the client and server

        Practices that work well for function calls in the same process can
        become incredibly inefficient when used

        between processes. Communication between functions can be very chatty,
        implementing behavior with lots of small, frequent calls between the
        participants. These participants also like to share data often pass by
        reference where all the participants share pointers to a single copy of
        the data, but they also pass by value where the caller receives its own
        copy of the data. Since pointers are difficult to use between
        processes, remote calls usually share data between processes using pass
        by value. But passing copies of large objects or data sets across the
        network harms performance as serialization takes time to perform and
        consumes memory and bandwidth. To make the communication efficient, the
        remote procedures need to be invoked less frequently and exchange less
        data.

        Access over common networks

        For cloud computing to be truly ubiquitous, the client and server need
        to support connecting over the public internet, since that is the
        network that connects everything. At the same time, when components in
        a Cloud Application are distributed, they need to support connecting
        over internal networks as well as the internet. The internal networks
        and the internet need to work the same so that clients and servers can
        connect over either as needed. Hypertext Transfer Protocol (HTTP) is

        universally used by modern systems yet has limited capabilities for
        connecting applications. Protocols like Distributed Component Object
        Model (DCOM) and Common Object Request Broker Architecture (CORBA) work
        for application integration but don’t work as well with worldwide
        networks optimized for HTTP.

        An application integration approach must overcome these challenges in
        order to allow clients and servers to work well together over the
        internet.

        Therefore,

        An application should expose a Service API consisting of tasks the
        application can perform. Implement the API as a web service to make the
        application easy to use in a cloud-native architecture.

        The Service API is a contract between a service provider (i.e., the
        service application) and a service consumer (i.e., the client). The
        provider implements the contract, and the consumers depend on it. The
        consumers can invoke any of the tasks in the Service API but do not
        know how the provider implements those tasks. The provider can change
        its implementation of the tasks without impacting the consumer as long
        as the provider does not change the API.

        As Figure 3-8 shows, the Service API defines a set of tasks that are the
        use cases the service application can perform. The service application
        implements each of those tasks so that each one performs the behavior
        it’s supposed to. The client can invoke any of the tasks, but it has
        access only to the definitions of the tasks, not to the service
        application’s internal implementations of the tasks. The set of tasks
        in the Service API is a contract between the client and service
        application. It is implemented as a web service so that the client and
        application can connect across the internet or any network built on
        internet technology, such as a data center’s internal network.





        Figure 3-8. Service API

        A Service API combines the application functionality of a
        service-oriented interface with the network protocol of a web service.
        It exposes a service-oriented interface as a web service that clients
        on the internet can invoke efficiently. This solution resolves all of
        the challenges of enabling a client and server to communicate
        effectively and efficiently over the internet, incorporating solutions
        that have already been developed for technologies other than cloud
        computing:

        Clean separation of client functionality from server

        functionality

        How can a client and server be separated into two separate sets of
        code?

        As computer programs have grown in complexity, the need to encapsulate
        functionality and make it reusable has become well understood.
        Procedural programming evolved into object-oriented programming. In
        object-oriented programming, the only way to interact with an object is
        through its interface—which is the set of messages to which the object
        can respond (Smalltalk-80,

        1983). A Facade (Design Patterns, 1994) defines a unified, higher-level
        interface for a set of interfaces in a subsystem, making the subsystem
        easier to use.

        An application programming interface (API) is an interface that is
        designed to be invoked by client code (rather than used by a human). An
        API makes an application easier to work with, enabling the application
        to expose a set of behaviors for clients to invoke while also enabling
        the application to hide its implementation. The API creates a clear
        separation between the client and application, acting as a contract
        between them. By using the API to hide its implementation, the
        application preserves its ability to change its implementation without
        impacting the clients, so long as it maintains its API. The client and
        server can evolve independently, and the client and server development
        teams can work independently, only needing to coordinate to develop the
        API itself. Often, the server team designs the API and the client team
        uses whatever the server team designed, so even that coordination can
        be pretty minimal.

        Remote access to the server from the client

        How can a client invoke a server remotely across a network?

        A procedural programming language supports function calls within a
        process—an object-oriented language supports invoking methods on
        objects within a process,

        but something more is needed for a client to invoke a server remotely
        across a network between processes. A Remote Procedure Invocation
        (Enterprise Integration Patterns, 2004) enables one application to
        invoke behavior in another application across a network. The behavior
        could be procedural, invoked via a remote procedure call (RPC), or it
        could be object-oriented, invoked via remote method invocation (RMI).

        Remote procedure invocation enables a client to invoke a server
        remotely. However, as the pattern explains, the fact that remote
        procedure invocation works so much like local procedure calls can
        actually become more of a disadvantage than an advantage. There are big
        differences in performance and reliability between local and remote
        procedure calls because the later occur over a network. Remote access
        enables a client and server to work remotely, but they will achieve
        rather poor performance.

        Efficient communication between the client and server

        How can a server expose its functionality so that a client can invoke it
        efficiently?

        A Session Facade (Core J2EE Patterns, 2003) or Remote

        Facade (Patterns of Enterprise Application Architecture, 2002) improves
        efficiency over a network by providing a course-grained facade on
        fine-grained objects. A Service

        Layer (Patterns of Enterprise Application Architecture, 2002) gathers
        multiple remote facades as services in a layer that encapsulates a
        domain model as a set of available operations that can also be made
        remotely

        accessible. Service Facade (SOA Design Patterns, 2008) generalizes
        services in a service-oriented architecture (SOA) that abstracts a part
        of the service architecture and increases its decoupling from the rest
        of the architecture.

        An API implemented as a set of service tasks encapsulates a set of use
        cases for what the application can do as well as for how clients will
        use the application. With a service interface, the application exposes
        its behaviors as a set of tasks it can perform for clients, enabling
        the client to treat the application as a service. When a client invokes
        a service task in the application, it can pass any context necessary as
        parameters in the invocation. When the application produces a result or
        error while performing the task, the invocation can return that result
        or error back to the client. Because large objects are expensive to
        transfer (that is, copy) across the network, the parameters

        and return values for each service task should be primitives and simple
        objects that are easy to serialize. Often a primitive is a unique
        identifier—a Claim Check

        (Enterprise Integration Patterns, 2003)—for a complex object, so that
        when the receiver wants to use the object, it can use the primitive to
        find the object in a shared data store and load it for use.

        Access over common networks

        How can a server expose its efficient application interface for use over
        the internet and similar internal networks?

        As the internet evolved into the World Wide Web (WWW), the hypertext
        transfer protocol (HTTP) became the common protocol of choice for
        web-based applications. HTTP enables a caller to specify not just the
        application listening on a port but also individual endpoints within
        that application. The firewalls, routers, browsers, and the rest of the
        backbone of the global internet support HTTP since it is already used
        to access web pages. This enables simpler connections between the
        user’s desktop and servers running backend code—new ports do not need
        to be opened for each application. Applications thus evolved to expose
        their functionality via HTTP as web services.

        While the concept of web services itself has become fairly stable, the
        protocol for performing web services has evolved over time. All of the
        protocols use HTTP as the universal transport, but they differ in the
        format of the data on that transport and in the schema to describe the
        protocol’s API and its data formats. The first major web service
        protocol was Simple Object Access Protocol (SOAP), which used
        Extensible Markup Language (XML) to define application interfaces
        expressed as Web Services Description Language (WSDL) that work much
        like the objects in object-oriented programming. SOAP was eventually
        replaced by Representational State Transfer (REST) protocol, which
        makes parts of an application available as resources that the client
        specifies using HTTP Uniform Resource Identifiers (URIs) and operates
        on using HTTP methods (such as GET, PUT, POST, and DELETE to CRUD
        resources as units of data). REST APIs can be published as Swagger
        documents that define the API as a contract. The service application
        implements the Swagger API’s contract and the client depends on the
        Swagger API’s contract to invoke service behavior. Specifications such
        as OpenAPI and gRPC standardize web service protocols for universal
        integration by development teams who are then able to otherwise work
        independently.

        Thus a Service API resolves the difficulties of making client/server
        interactions work well.

        Service API incorporates and expands upon the practice

        explained in The Twelve-Factor App: VII. Port binding:

        The web app exports HTTP as a service by binding to a port,

        and listening to requests coming in on that port… .The port-

        binding approach means that one app can become the

        backing service for another app, by providing the URL to the

        backing app as a resource handle in the config for the

        consuming app.

        A Service API defines a service-oriented API that clients must adhere to
        as they access the service. A Service API can be easily implemented as
        a border for remote access, making the application accessible across a
        network connection by any client running in a separate process.



        A Service API creates a clean separation between an application and the
        clients that use it, reducing coupling between them, making both easier
        to implement, and enabling them to evolve independently as long as they
        preserve the API. It can support remote access, providing
        course-grained tasks that make remote invocation more efficient.

        One of the biggest challenges to applying Service API is designing the
        API. It must make the producer’s functionality available while hiding
        the implementation details. Once an API is put into use, it can be
        difficult to evolve, often requiring an API versioning strategy.

        A service can be stateful or stateless. A Cloud-Native Application

        with a Service API is typically implemented to run as a Stateless

        Application .

        These services are often part of a Microservices Architecture

        (Chapter 4). Services with broad responsibilities can be

        implemented by a Service Orchestrator that orchestrates other services
        with more specialized responsibilities. Services can

        also be choreographed more loosely in an Event-Driven

        Architecture (Chapter 6).

        Examples

        An easy way to understand APIs is as the interface feature in languages
        such as Java. The interface’s functionality should be abstracted as a
        service capability comprised of service tasks. An interface is a
        contract between the object and its client that separates what the
        object needs to be able to do from the class that implements how it’s
        done.

        OpenAPI is the prevailing industry standard to publish a web Service API
        as a contract. It’s typically implemented using Swagger to create a
        REST over HTTP web service. The service application implements the
        OpenAPI contract, and the client depends on the OpenAPI contract to
        invoke service behavior. gRPC is an alternative to REST that defines a
        web Service API as an RPC instead of resources.

        Java interface

        Here is a service that converts money from one currency to another. It
        has a very simple Service API that performs a single task, convert .

        First, let’s specify the money conversion Service API as a Java

        interface. Example 3-3 shows the code to create a Java interface named
        MoneyConverter that declares a single convert method.

        Example 3-3. Java interface for MoneyConverter

        import java.math.BigDecimal;

        import java.util.Currency;

        public interface MoneyConverter {

        public BigDecimal convert(BigDecimal amount, Cu }



        The convert method accepts an amount of money in one currency ( from )
        and returns the amount in another currency ( to ). It is an interface,
        so it does not implement the method, just declares its signature. Each
        method in a Java interface is

        essentially a Template Method (Design Patterns, 1994), except that
        rather than implement the skeleton of an algorithm, an interface method
        implements no algorithm at all. This sort of interface that defines
        methods for performing tasks is the essence of a Service API.

        A class that actually performs the conversion implements the

        interface. Example 3-4 shows MyConverter , which

        implements the MoneyConverter shown in Example 3-3.

        Example 3-4. Java class for MyConverter

        import java.math.BigDecimal;

        import java.util.Currency;

        public class MyConverter implements MoneyConverte public BigDecimal
        convert(BigDecimal amount, Cu

        /* Code that converts the amount from one cu

        }

        }



        A client that needs the conversion performed delegates the

        work to an instance of MoneyConverter . Example 3-5 shows how the
        converter object, myConverter , is initialized as an instance of
        MyConverter , the concrete class with code that actually performs the
        conversion.

        Example 3-5. Java client code using MyConverter as a MoneyConverter

        BigDecimal unconvertedMoney = 1000.0; Currency originalCurrency =
        Currency.getInstance Currency newCurrency = Currency.getInstance
        ("USD BigDecimal convertedMoney = null;

        MoneyConverter myConverter = new MyConverter();

        convertedMoney = myConverter.convert(unconvertedM

        originalCu

        // For example, 1000.00 Indian Rupee equals 12.23 System.out.println
           (unconvertedMoney + " " + origi

        + " equals " + convertedMoney + " " +

        After myConverter is initialized, all subsequent code treats it as a
        MoneyConverter , not knowing whether the converter object is actually
        an instance of MyConverter or some other concrete class. This makes the
        code able to handle any concrete class that implements the
        MoneyConverter interface. The interface, MoneyConverter , is a contract
        between the client and the concrete class, MyConverter . The majority
        of the client code just knows the object implements the contract
        represented by the interface, so it can use an instance of any concrete
        class that implements the interface.

        JAX-RS interface

        The MoneyConverter service can only be used locally within a Java
        program. Let’s use the Java API for RESTful Web Services (JAX-RS) to
        expose this local service as a web service.

        Example 3-6 shows the web service declaration. Its root URI is

        /api .

        Example 3-6. JAX-RS web service declaration

        import javax.ws.rs.*;

        import javax.ws.rs.core.*;

        @ApplicationPath("/api")

        public class RestApplication extends Application }



        Example 3-7 shows the resource CurrencyResource , which has a convert
        method. It’s implemented using the

        MyConverter class from Example 3-4.

        Example 3-7. JAX-RS web resource

        import java.math.BigDecimal;

        import java.util.Currency;

        import javax.ws.rs.*;

        import javax.ws.rs.core.*;

        @Path("/currency")

        public class CurrencyResource { @POST

        @Path("/convert/")

        @Consumes(MediaType.APPLICATION_FORM_URLENCODED @Produces
         (MediaType.TEXT_PLAIN) public String convert(@FormParam
         ("amount") Stri

        @FormParam("from") String

        @FormParam("to") String t

        BigDecimal unconvertedMoney = new BigDecimal

        Currency originalCurrency = Currency.getInsta

        Currency newCurrency = Currency.getInstance(t

        BigDecimal convertedMoney = null;

        MoneyConverter myConverter = new MyConverter

        convertedMoney = myConverter.convert(unconve

        originalCu

        return convertedMoney.toString();

        }

        }



        When a web service client invokes

        /api/currency/convert with an HTML form

        containing the three parameters, it gets a response containing the
        converted money.

        Go interface

        Like Java, the Go language also has an interface feature. The

        code in Example 3-8 declares a MoneyConverter interface using the types
        Float and Currency.

        Example 3-8. Go interface for MoneyConverter

        type MoneyConverter interface{

        Convert(amount Float, from Currency, to Currenc }

        OpenAPI interface

        A Swagger document for our API would include a /convert path. It
        requires the usual three input parameters: amount ,

        from , and to . And it returns a number. (See Example 3-9.)

        Example 3-9. OpenAPI document for Convert task

        openapi: 3.0.0

        . . .

        paths:

        /convert:

        post:

        description: Convert money from one currenc

        requestBody:

        required: true

        content:

        application/json:

        schema:

        type: object

        required:

        - amount

        - from

        - to

        properties:

        amount:

        type: number

        from:

        type: string

        to:

        type: string

        responses:

        '200':

        description: Successfully converted the

        content:

        application/json:

        schema:

        type: number
        """,
    "Stateless Application":
        """
        Stateless Application

        You are developing an application with a Cloud-Native

        Architecture that has a Service API . You want it to scale easily, shut
        down cleanly, and recover from failures gracefully.

        How can an application support concurrent requests efficiently and
        recover from failures without losing data?

        Applications, whether hosted on the cloud or traditional IT, manage two
        types of state: session state is data used temporarily and limited to a
        single user; domain state is data used long term and is available to
        all users in all sessions, and it can even be shared between different
        applications.1

        Developers creating applications for traditional IT have learned that
        they can improve application performance by loading domain data into
        the application and keeping it there. Applications store domain
        data—data that is available to all applications and services across all
        transactions—in databases to keep it safe and so they can share it.
        When database access is slow—due to overloaded data center networks,
        inefficient disk drives, and data locking and contention—an application
        can provide better throughput by prefetching any data that might be
        needed, caching it in memory, and never letting go because it might
        eventually be needed again.

        Storing domain data read-only in an application causes a couple of
        problems:

        Performance

        Holding data in memory helps improve performance by responding to client
        requests faster without having to retrieve data from a slow database,
        but hurts performance by making the application start slower and spend
        CPU managing the copies of the data. Prefetching data takes time, which
        makes the application’s startup

        take longer. The application can avoid prefetching by only caching data
        the first time it’s retrieved, but that hurts the throughput for users
        waiting for uncached data to be retrieved the first time.

        Scalability

        Each object will hold its own copy of the same data. Storing so much
        data in memory causes the application to run out of memory
        sooner—limiting scalability. Multiple objects could try to share the
        same data, but then they have to implement a shared cache, which gets
        complicated. To avoid running out of memory, the objects could limit
        how much data they will cache, but then they need to implement an
        eviction policy for removing cached data so that more data can be
        added.

        An application that delays persisting the changes it makes to domain
        data can suffer even bigger issues:

        Consistency

        When multiple objects each hold their own copy of the same data and one
        of them changes that data, only one copy gets updated. The other
        objects continue to use old copies that haven’t been updated. Stale
        copies of data

        mean that different users get different answers based on what is
        supposed to be the same data.

        Graceful shutdown

        To shut down a stateful application cleanly, before the application can
        shut down, any changes in its data must be persisted first by writing
        all of the data—or at least the data that has changed, if the
        application knows which data that is—to that slow database that the
        application has been avoiding. If the application crashes, all those
        data changes are lost.

        Recoverability

        A stateful application’s tendency to lose data changes when it crashes
        wreaks havoc on disaster recovery (DR). A DR strategy tries to minimize
        the recovery point objective (RPO), which is the point before the
        application crashed that can be recovered. All changes in the
        application after the RPO are lost, which is why a DR strategy strives
        to keep the RPO short. A stateful application is an RPO tragedy waiting
        to happen. If an application enables users to make data changes but
        persists those changes only once an hour, the RPO effectively becomes
        an hour. When the application crashes, all of those changes the users
        thought they had made as long as an hour ago are lost. When DR

        restarts the application, it will not have those users’ changes.

        An application can avoid these issues by not caching domain data in
        memory.

        An application that stores session data limits how many users it can
        support. When an application ran on a user’s desktop computer, it
        needed to support only that one user. But when client/server computing
        technologies like Java 2, Enterprise Edition (J2EE) moved the
        application’s business logic back onto the server, multiple users
        became able to access a single copy of the application.

        How can an application on the server support multiple users? A client
        interacts with the application repeatedly via a session that associates
        the client’s calls. The session includes session data—data gathered
        from the history of what the client has done.

        Where should session data be stored? For web browser clients, that
        somewhere becomes an HTTP session object, server objects that servlets
        use to support web browsers running on the client. Each user’s browser
        has its own HTTP session that keeps session data on the server, which
        greatly improves performance because it avoids sending data back to the
        browser using what is (or used to be) often a very slow internet
        connection.

        HTTP sessions create their own scalability problems. Each user’s browser
        has its own HTTP session object, so a server is limited in how many
        browsers it can support by how many HTTP sessions it can host.
        Furthermore, each browser has to send its series of requests to its own
        HTTP session, not any others. The browser stores its HTTP session’s
        identifier in a cookie named JSESSIONID, which the server uses to
        implement sticky sessions where a browser’s requests are always routed
        not just to any HTTP session but to the specific HTTP session with that
        session ID. While keeping session data on the server helps avoid
        performance problems caused by slow network bandwidth, the trade-off is
        scalability problems that limit how many concurrent users an
        application on the server can handle.

        As long as session data is stored on the server, there will always be a
        limit how many concurrent users an application on the server can
        handle. As long as an application stores domain data in memory, the
        application will run into problems with performance, scalability,
        consistency, graceful shutdown, and recoverability.

        Therefore, Design the application as a Stateless Application that stores
        its domain state in databases and receives its session state as
        parameters passed from the client.

        What makes an application stateless is not that it has no state but that
        it stores its state elsewhere, which makes it more scalable and
        resilient.





        Figure 3-9. Stateless Application

        As shown in Figure 3-9, a Stateless Application has three parts: the
        Stateless Application, its databases where it stores its domain state,
        and its clients, each of which separately holds its own session state.
        The application still operates on domain state, but it stores that
        state in databases, not in the application. The application uses
        session state to decide what to do, but it doesn’t store session state;
        it gets the context for performing requests as parameters to the
        request. Each application client maintains its own session state and
        uses it to populate the parameters in each of its requests. For
        example, the client might pass in a bank account number or a product ID
        from its session state, then the Stateless Application uses that
        parameter to load the bank account or product details from it domain
        database.

        Making an application stateless resolves the problems with a stateful
        application:

        Performance

        The Stateless Application doesn’t spend bandwidth populating the cache
        and CPU managing the cache.

        Scalability

        The Stateless Application doesn’t spend memory duplicating data that is
        already stored in databases.

        Consistency

        The Stateless Application doesn’t duplicate data from the database, and
        so it cannot get out of sync; it is always in sync with the database.

        Graceful shutdown

        The Stateless Application is always ready to shut down cleanly between
        business transactions. The application can be quiesced to finish
        performing business transactions before shutting down.

        Recoverability

        When a Stateless Application crashes, the only data that is lost is
        changes in any business transactions that did not complete
        successfully. The application can minimize these by keeping its
        business transactions brief. All other domain data is persisted to the
        databases and can be recovered easily.

        A Stateless Application can perform requests concurrently for multiple
        clients because they each have the same state—which is no state. It
        performs each business transaction in its own thread with its own
        context from the request that loads the domain data it needs from the
        database. When the application finishes performing the business
        transaction, the thread ends and the data is discarded, making the
        application stateless once again.

        The drive toward applications with no session state arose with web
        services—which work the way the WWW does and are accessed via faster
        internet connections. Each web service is

        stateless; the Client Application —be it a web application, a mobile
        application, a CLI, or a chatbot—is responsible for maintaining session
        state and passing it to the web service as parameters. Each client
        typically runs on its own computer, so the solution scales quite well.

        Most applications have domain state, so if the program is stateless,
        where does the state go? The application stores

        domain data in Backend Services , such as databases. Cloud

        platforms typically provide numerous different Cloud Database services.

        A Stateless Application loads its domain state from storage while it
        performs work for a client. Each call to the Service API defines a
        logical transaction. The application can cache data temporarily during
        the transaction but not between transactions. Concurrent transactions
        in the same Stateless Application each run in a separate thread that
        caches its own data. At the beginning of a transaction, a Stateless
        Application uses the context in the request parameters to find and load
        the relevant domain data from the database to perform business logic.
        At the end of a successful transaction, a Stateless Application stores
        any updates to the data back to the database before returning a result
        to the client. After a transaction, a Stateless Application effectively
        flushes all of its data before starting the next transaction.

        As explained in The Twelve-Factor App: VI. Processes, applications
        should persist their data:

        Twelve-factor processes are stateless and share-nothing.

        Any data that needs to persist must be stored in a stateful

        backing service, typically a database. The memory space or

        filesystem of the process can be used as a brief, single-

        transaction cache.

        The practice goes on to say that an application also should not store
        session data:

        Sticky sessions are a violation of twelve-factor and should

        never be used or relied upon. Session state data is a good

        candidate for a datastore that offers time-expiration, such

        as Memcached or Redis.

        Stateless services are the building blocks for service-oriented

        architecture (SOA). “Service Statelessness,” Chapter 11 in SOA:

        Principles of Service Design (2016), discusses at length how to design
        stateless services.



        Statelessness enables an application to start quickly and shut down
        cleanly and simplifies crash recovery. To shut down a stateful workload
        cleanly, the platform must first persist the state. To restart a
        stateful workload, the platform must start the workload and then load
        its persisted state before making the workload available to handle
        client requests. When a stateful workload crashes rather than being
        shut down cleanly, the platform doesn’t have the opportunity to persist
        its state first, and so that state is lost. These problems go away when
        the workload is stateless. A stateless workload is much easier to
        quiesce and shut down with no data loss because it doesn’t have any
        state that needs to be persisted. It is easier to restart because it
        doesn’t have any state that needs to be reloaded. When a stateless
        workload crashes, the only state that is lost is the intermediate state
        of logical transactions that haven’t yet completed, so the lesson is to
        keep those transactions brief and that intermediate state small and
        persist it quickly.

        A challenge for a Stateless Application is that retrieving the same
        domain data repeatedly may degrade network performance between the
        application and its database. This can be remedied with a caching
        service, which keeps the application stateless. Likewise, if a client’s
        session state becomes extensive, it may degrade network performance
        between the application and its client. This encourages designing an
        API with parameters that are few and simple, limiting the session state
        that is necessary.

        Statelessness makes scalability much easier. Making an

        application into a Replicable Application —one that scales the way cloud
        scales—is much more complex when the replicas have state. When the
        replicas are stateful, the platform must use sticky sessions, a
        technique from traditional IT that should be avoided in the cloud.
        Furthermore, each replica’s state has to be duplicated or persisted so
        that it’s not lost if the replica crashes or needs to fail over. With a
        Stateless Application, all of the application’s replicas are equivalent
        because they’re all stateless. All replicas have the same data because
        it’s all stored in a shared database. Routing is simpler—any replica
        can serve any client request because they’re all equivalent. When
        scaling in, it does not matter which replicas the platform selects to
        shut down because they’re all equivalent.

        A Stateless Application is easier to implement when it has a

        Service API . The workload doesn’t expose its state via the API— it
        doesn’t have any state to expose. Rather than expose the domain state
        that it manages, the workload should use its API to provide tasks that
        keep the state encapsulated and hidden from the client and limit the
        scope of the session state.

        A Stateless Application with a Service API is a stateless service, which
        is the preferred model to implement functionality in a cloud-native
        architecture. It is the basis for implementing a

        Microservice .

        If an application still wants to cache domain data to improve

        performance, it should use a Backend Service , that is, an in-memory
        database, such as Redis or Memcached.

        Examples

        When a team that is new to cloud-native architecture is told that their
        application needs to be able to run statelessly, their first reaction
        typically is to say that their application won’t work that way. “You
        don’t understand,” they explain, “our application has state.” No
        kidding. Every application more complicated than a calculator has
        state. The trick is to figure out what in the application’s
        implementation is storing data and move the data outside your program.
        In a sense, this is a form of functional programming, and if your
        language of choice supports functional programming constructs, it may
        be easier to implement these approaches in that way. Two common ways of
        storing data in your application can be addressed with these fixes:

        Make domain state external

        Make session state external Make domain state external

        With traditional IT, it is common to cache data from the database so
        that it only has to be fetched once. The most common way to do this is
        to define an instance variable to keep cached data. When retrieving a
        piece of data, retrieve it from the cache; if it’s not already in the
        cache, first load it from the database into the cache, then retrieve it
        from the cache. A very

        simple version of the code (in Java) looks like Example 3-10.

        Example 3-10. Stateful ProductManager stores products

        public class ProductManager {

        private Map products; // products i

        private Database getDatabase() {

        Database database;

        database = /* Get the database connection

        return database;

        }

        public getProductNamed(String name) {

        Product product = products.getOrDefault(n

        if (product == null) {

        product = this.getDatabase().get(name

        products.put(product.name(), product

        }

        return product;

        }

        }



        If you want your application to be stateless, the object should be
        stateless. So, don’t cache the data, retrieve it from the database

        every time. As shown in Example 3-11, the class no longer declares an
        instance variable, and the getProductNamed() method becomes much
        simpler.

        Example 3-11. Stateless ProductManager does not store products

        public class ProductManager {

        // Do NOT declare a products instance variabl

        private Database getDatabase() {

        Database database;

        database = /* Get the database connection

        return database;

        }

        public getProductNamed(String name) {

        Product product = null; // products is a

        product = this.getDatabase().get(name);

        return product;

        }

        }



        But won’t this stateless version be inefficient? In the cloud, databases
        have gotten faster, especially if they’re NoSQL databases and have
        their own caches. Network connections have gotten faster. Run multiple
        replicas of the database so that

        each replica has less work to do and can do it faster; see Cloud

        Database . If data still needs to be cached in memory, use a Backend
        Service specialized for that purpose, such as Redis or Memcached.
        Making the database faster and the application stateless will
        ultimately be a much better solution.

        Make session state external

        Session state refers to an application’s data that is unique to a
        particular user. When processing multiple requests that are related
        through a common interaction with a user, session state is that data
        that needs to be carried across all of those requests. For example,
        session state might include the identity of a user, so that the right
        records could be fetched back from the database using the approach
        previously described. The user identity can’t only be in the database,
        because it’s part of the key that’s used to find the right data.
        Luckily, there are approaches to externalize session state as well.

        The most common approaches involve storing a key (such as the user’s
        identity) in something that is attached to every user request. In the
        example of a request carried over HTTP, this could be in the contents
        of an HTTP cookie or in the parameters of the request itself.
        Regardless of which protocol or framework you are using, that’s the
        usual approach—make sure that a top-level key that is associated with
        the user gets passed in with each request.

        However, even in this case, there is the temptation to store this
        information within the program, typically in a Singleton

        (Design Patterns, 1994) or in a class variable. Similar to the example
        above, classes should use temporary variables, not instance variables.
        Temporary variables passed as parameters are part of the thread running
        the method, so each thread gets its own copy, and the variables’
        lifetime ends when the thread does. That means that your class can be
        completely threadsafe, which makes debugging easier.

        The side benefit of following these approaches is that the application
        is now a Replicable Application. Not only does it not matter if any
        particular copy of the application fails and is restarted (because no
        state is stored in the application), but it also does not matter how
        many copies of the application are running and receiving requests at
        any time, because all copies can handle any request equally well.
        Statelessness is difficult to achieve in that it takes more work to
        think about developing applications in this way, but the benefits are
        often well worth the trouble.
        """,
    "Replicable Application":
        """
        Replicable Application

        (aka Horizontally Scalable Application)

        replicable adjective

        rep· li· ca· ble (ˈre-plə-kə-bəl)

        that which can be replicated

        that which can be produced again to be exactly the same as before

        You are developing an application with a Cloud-Native

        Architecture encapsulated in an Application Package . You want your
        application to always be available, even though the cloud can be
        unreliable and client load can grow greater than a single instance of
        the application infrastructure can handle.

        How can an application run reliably on an unreliable platform and scale
        to handle greater client load the way the platform scales?

        When developers of applications for traditional IT are asked how
        reliable their application is, they often reply, “My application is as
        reliable as the hardware it’s running on.” In this way, traditional IT
        applications punt responsibility for reliability and make it the
        responsibility of the hardware engineers and operations staff to make
        their IT environments reliable. This also avoids the uncomfortable
        truth that sometimes applications fail even when the hardware is
        functioning properly. These failures can have many causes, such as
        memory leaks, deadlocked threads, blocked I/O connections, or storage
        issues.

        There are limits to how reliable hardware can be, not to mention the
        reliability of the OS and other system services the application depends
        on. As the reliability of hardware goes up, the price tag rises even
        faster—mainframes cost more than commodity computers, RAID arrays cost
        more than simple storage. Even if hardware can be made to fail
        infrequently, that only lowers the frequency of unplanned outages; it
        doesn’t eliminate them completely. Furthermore, there are also planned
        outages—from OS patches to system upgrades—that cause the
        ubiquitous “system is currently unavailable because of maintenance”
        status that systems frequently display on weekends and holidays.(Not to
        mention that planning maintenance outages at times that avoid
        inconveniencing the users requires that the operations staff spend
        their weekends and holidays at work upgrading systems. And they do so
        with the ever-present threat that they’d better have their work
        completed and the system functioning again by Monday morning!)

        Cloud computing embraces a new perspective: nothing is truly reliable,
        including computer systems. Rather than wasting money on trying to make
        your systems infinitely reliable, it’s more practical and cost
        effective to design them to be redundant in the hope that even as some
        parts fail—or are intentionally shut down for maintenance—other parts
        will keep operating, thereby keeping the overall system reliable. This
        approach enabled one vendor who embraced cloud techniques to
        intentionally purchase RAM chips with a greater failure rate because
        they were cheaper. If the vendor found that a batch of RAM chips was
        too reliable, they assumed that they were being overcharged and that
        they should be able to get less-reliable chips instead at a
        significantly better price.

        Accepting that hardware is unreliable recognizes the problem but doesn’t
        solve it: How can a Cloud-Native Application run reliably even when a
        cloud platform is less reliable? The key is to not only structure the
        hardware as redundant parts but to structure the application as
        redundant parts as well.

        Meanwhile, an application running in the cloud is shared by numerous
        users. When many of them start using the application at the same time,
        it can become overloaded with more client requests than it can handle.
        Some user requests may still get processed efficiently, and to them the
        application will still seem reliable. But for others, either their
        requests suffer very poor performance, or requests get lost and ignored
        completely, or the application becomes overloaded and crashes. Whatever
        the problems, the application becomes less reliable, even on reliable
        hardware, when too many users create too much load.

        Ideally, the application should be reliable for all users at all times.
        With traditional IT, there are two main approaches for providing
        capacity for client requests:

        Vertical scaling

        Grow the application to use more of its computer’s capacity.

        Maximum sizing

        Size the application to handle the maximum client load that can occur.

        Vertical scaling requires that the application is able to access
        additional CPU and memory capacity in its computer. The application
        uses this additional capacity to serve more concurrent client requests.
        The application cannot grow once the computer runs out of CPU or memory
        and can also become constrained when it is using all of the computer’s
        network bandwidth or storage. While an application can scale up
        vertically, it often cannot scale down again—memory and storage, once
        acquired, can be difficult to release, often at a minimum requiring the
        process to restart.

        Maximum sizing ensures reliability at all times by determining the
        maximum client load that is likely to occur, then sizing the
        application for that. The problem is that most of the time the client
        load is much less and the application uses only a fraction of its
        capacity. An application that reserves a lot of capacity but uses much
        less of it is wasting money paying for capacity that it is not using.
        And however high the application’s maximum client load may be, there’s
        always the possibility it could receive even greater load and still
        become unreliable.

        How can a Cloud Application reserve a lot of capacity when it has a lot
        of client load but less capacity when it has less load, so that its
        capacity is always proportional to the current level of client load?
        And how can the application always have the capability to grow more and
        more if it needs to? The key is to structure the application to scale
        bigger and smaller as client load increases and decreases.

        The application should run as redundant parts for reliability and should
        be able to scale bigger and smaller as client load changes.

        Therefore,

        Design the application as a Replicable Application that is able to run
        as multiple redundant application replicas that all provide the same
        functionality without interfering with one another.

        By designing a Cloud-Native Application to be replicable, the cloud
        platform will be able to deploy replicas of the application.





        Figure 3-10. Replicable Application

        As Figure 3-10 shows, the cloud platform’s management functionality
        includes an application deployer, which performs the function of
        creating a new workload instance of an application from its Application
        Package. When cloud management runs the deployer repeatedly, it creates
        multiple replicas of the application.

        Because a Cloud-Native Application is encapsulated as an Application
        Package, the cloud platform can easily create new replicas of the
        application by deploying the package repeatedly. Each replica is a
        deployment of the same Application Package, so all of the new replicas
        are equivalent. The replicas run independently of one another, do not
        even know about one another, and do not interfere with one another.

        Application replication is a fundamental feature in most cloud
        platforms. Platforms that provide autoscaling use replication for that
        as well, but autoscaling isn’t a requirement of replication. Some
        examples include the following:

        Amazon EC2

        EC2 Auto Scaling adds EC2 instances when demand spikes

        Kubernetes ReplicaSet

        Guarantees the availability of a specified number of identical Pods

        Azure Function

        As requests increase, Azure automatically runs more functions

        IBM Cloud “Auto Scale” for VPC

        Dynamically creates virtual server instances to improve performance
        based on metrics like CPU, memory, and network usage

        With each of these examples, the platform is able to deploy new replica
        instances of the application that are equivalent to existing replica
        instances, such as to start an application by deploying redundant
        replicas or to replace a replica that has crashed or become
        unresponsive.

        The cloud platform treats multiple replicas of an application as a group
        and makes the group behave like one big copy of the application.
        Running multiple replicas rather than one big replica solves both of
        the challenges of making an application more reliable than its
        hardware:

        Scalability

        Each replica can run on a different computer, providing the capacity of
        multiple computers, which is greater than the capacity of any single
        one of those computers.

        Reliability

        If one computer fails, only the replicas running on that computer fail;
        the rest of the replicas keep running.

        The multiple replicas provide greater capacity for serving more
        concurrent client requests than a single replica could. While all of
        the replicas could run on a single computer, running on multiple
        computers enables them to use the capacity of multiple computers. When
        a computer fails, only the replicas running on that computer fail; the
        rest of the replicas keep running, making the application highly
        available and providing greater reliability for the clients.

        The application can run as a single replica, but as explained in

        The Twelve-Factor App: VIII. Concurrency, “The application must also be
        able to span multiple processes running on multiple physical machines.”
        A significant advantage of this approach is that scalability becomes
        much simpler: “The process model truly shines when it comes time to
        scale out. The share-nothing, horizontally partitionable nature of
        twelve-factor app processes means that adding more concurrency is a
        simple and reliable operation.” Each workload replica can still employ
        other techniques for scaling: “An individual process can handle its own
        internal multiplexing, via threads inside the runtime, can support the
        async/evented model, and vertical scaling is possible.”

        The application can not only scale out to add capacity, it can also
        scale in and reduce capacity simply by shutting down some

        of the replicas. As explained in The Twelve-Factor App: IX.

        Disposability:

        The twelve-factor app’s processes are disposable, meaning

        they can be started or stopped at a moment’s notice. This

        facilitates fast elastic scaling, rapid deployment of code or

        config changes, and robustness of production deploys.

        For an application to be replicable, avoid anything that fits the

        the Singleton pattern (Design Patterns, 1994) in which an object has
        only a single instance that cannot be replicated and must be shared
        globally. Avoid any design details that mean the application can run
        only as a single workload and therefore on a single computer, such as
        components with shared memory, concurrency semaphores, or a fixed IP
        address or domain name. Such designs were common with traditional IT,
        but they cannot support multiple copies in the cloud.

        Fortunately, business applications and many multiuser environments
        typically replicate easily. When the user buys a book, views a bank
        account, or browses movies to stream, the business transaction is
        implemented by a logical thread performed in a slice of the application
        architecture from the graphical user interface (GUI) through the
        business logic to the database and back. A replica may have capacity to
        handle tens or hundreds of such transactions in isolated, concurrent
        threads. Multiple replicas can handle many more, each handling its
        share of the total concurrent transactions and none of them interacting
        with one another except for updating shared Backend Services.



        A Replicable Application can run multiple redundant copies of itself
        without them interfering with one another. The cloud platform is what
        deploys the replicas. The cloud platform makes multiple replicas of the
        same application work like one big application, which improves the
        application’s scalability and reliability. Replication works well for
        typical business applications.

        However, developers who have never designed an application to be
        replicable often find doing so a challenge. Traditional IT developers
        are accustomed to designing an application with a single replica that
        scales vertically. The number one enemy of replication is the Singleton
        pattern and variations thereof— such as block storage and fixed IP
        addresses. These should be avoided.

        The cloud platform will have an easier time distributing requests across
        replicas and scaling them in if the application is

        a Stateless Application . Stateful replicas require that the load
        balancer implement sticky sessions, a technique that the cloud avoids.
        When replicas are stateless, they are all equivalent, not only when new
        replicas are created from the same Application Package but throughout
        their lifetimes. To scale in, any stateless replica is an equally valid
        candidate to be shut down because they are all equivalent.

        While replicas do not know about one another, they do

        coordinate via shared Backend Services . Because all of the replicas of
        an application share the same set of Backend Service instances, they
        all have access to the same external functionality and state—helping
        them all work the same way.

        Replicas often share a common set of domain data in a shared

        Cloud Database . Many cloud databases are able to replicate across
        multiple computers and storage, thereby scaling the same way the
        application does. A distributed database has better high availability
        and throughput than a database running in a single server. The
        application should avoid managing its own storage directly by employing
        measures such as a file system or especially block storage—which
        typically cannot be shared, as that can break the equivalency of the
        replicas.

        This ability to dynamically replicate on demand is a key

        advantage of a Microservice , which enables part of an application to
        scale rather than the entire monolith.

        Application replicas typically are not simply copies of the Application
        Package, but rather are copies of a virtual machine

        image (see Virtualize the Application ) or container image (see

        Containerize the Application ) that includes the Application Package.
        One advantage of packaging an application as an Application Package is
        that the package makes it easier for the cloud platform’s application
        deployer to deploy the application simply and reliably. By packaging
        the Application Package as a virtual machine or container, it is even
        easier for the application deployer to deploy repeatedly.

        Examples

        When a team that is new to cloud-native architecture is told that their
        application needs to be able to run multiple copies simultaneously,
        often their first reaction is to say that their application won’t work
        that way. The trick is to figure out what in the application’s
        implementation prevents multiple replicas running at the same time from
        working correctly. The following are some typical problem scenarios
        that would occur if multiple replicas of the application were running
        at the same time:

        The application depends on a Singleton (Design Patterns,

        1994). Managing a Singleton within a replica may be

        straightforward, but managing it across replicas is complex.

        They will interfere with one another—such as overwriting

        one another’s data—and keep any of them from working.

        They will each store their own data—such as in their own

        disk storage—and each will work but will not know about the

        data in the other replicas.

        The first replica will establish a lock on a resource, and the

        others will block while waiting to establish their own locks

        on the same resource.

        To establish a lock on a resource only once, all of the replicas

        will coordinate to elect one replica that will establish the lock

        that they will all then share. This might work until the replica

        that established the lock crashes without releasing the lock.

        Then, none of the replicas work, including the replacement

        for the replica that crashed.

        A scenario similar to a resource lock is an application that

        can run only on a particular IP address. The first replica

        reserves that IP address and assigns it to its network

        interface, then the other replicas cannot use it.

        A theme here is that typically multiple replicas work OK internally; the
        problem is how they use external resources and that the program was
        designed with the assumption that it would be the only replica using
        the external resource. The trick is to discover where these problem
        scenarios occur in the program, discover the design assumptions that
        led to the problem, and redesign that part of the program with better
        assumptions that eliminate the problem and enable replication.

        Here is some detail about a few specific examples:

        Avoid Singletons.

        Store data in a shared database service, not in disk storage.

        Manage a connection pool using an integration service.

        Avoid Singletons

        An application that uses the Singleton pattern will have difficulty
        running application replicas. When the application runs, it will create
        a single instance of an object that all of the application will share.
        If the application is run twice, each replica of the application will
        create its own Singleton. Two threads running in an application replica
        will share the same Singleton, but two threads running in two separate
        replicas will each access its replica’s Singleton, which usually
        defeats the purpose of making the object a Singleton. If two threads
        can successfully use two different Singleton copies, the object doesn’t
        need to be a Singleton.

        Perhaps the application can be structured such that the first replica
        creates the Singleton, then subsequent replicas will all access the
        Singleton in the first replica. This creates a couple of problems.
        First, it is complex to implement, with each new replica needing to
        know that the original replica already exists and how to access it and
        its Singleton. Second, any network problems between the replicas will
        make accessing the Singleton slow and unreliable. Third, if the first
        replica—the one with the Singleton—crashes, none of the other replicas
        will work because they have lost access to the Singleton. The surviving
        replicas need to detect that the Singleton is lost and create a new
        one, working together to ensure that only one of the surviving replicas
        creates the replacement and they all know how to access it.

        Rather than confront this coding complexity, a much simpler approach is
        to design an application to avoid any Singletons. Then, it is easy to
        run as a Replicable Application. Store data in a shared database
        service, not in disk storage

        An application that stores data directly in block or file storage will
        be difficult to replicate. It should instead use a database that the
        replicas can share.

        An application has some data to persist, so it creates a block storage
        volume and stores blocks of data. The problem with running multiple
        replicas of the application is that each one creates its own storage
        volume and stores its own data, but each replica knows only the data it
        stores in its volume and has no access to the data the other replicas
        have stored in their volumes. This is an even bigger problem if any
        replicas shut down or crash—the data in those replicas’ volumes becomes
        inaccessible, effectively lost.

        Rather than each replica creating its own volume, they could create one
        volume and share it. The first replica does not find the volume creates
        it, then subsequent replicas find the existing volume and also attach
        to it. This will not work because block storage volumes typically
        cannot be shared by more than one workload process. Even if they could,
        how would each replica know about the blocks stored by the other
        replicas while avoiding overwriting one another’s data? The application
        might be able to implement enough functionality to solve all of these
        constraints, but in doing so would end up implementing its own
        database.

        While traditional IT applications used to implement their own data
        persistence, Cloud Applications don’t have to. Instead, the solution
        for a Cloud Applications is to store its data in a database that has
        been created in a platform-managed database service and can be shared
        by multiple replicas of the application. This can even be a relational
        database or some other database running in a single server. The
        database coordinates requests from multiple threads—whether they are
        running in the same application replica or in different replicas —and
        coordinates writing data to blocks, remembering where the blocks are
        and avoiding overwriting blocks in use. As new application replicas are
        started and old ones are shut down, they all continue to share the same
        database. Such database services already exist, so no application
        should write its own.

        See Cloud-Native Storage (Chapter 7).

        Manage a connection pool using an integration service

        A Replicable Application can grow big enough to overwhelm a legacy
        system of record (SoR). Care must be taken in the application’s design
        to avoid this problem.

        When an application accesses an SoR, the SoR can typically handle only a
        limited number of concurrent connections. Too many concurrent connects
        will result in a crash. If the SoR can handle only 10 concurrent
        connections, the application creates a connection pool with 10
        connections, perhaps using a programming language’s connection pooling
        framework such as Java EE Connector Architecture (JCA). It channels all
        access through the pool so that it uses up to 10 connections at the
        same time. The problem with running multiple replicas of the
        application is that each one creates its own connection pool, each with
        10 connections. Multiple application replicas using 10 connections each
        can create more than 10 concurrent connections to the SoR and crash
        it.

        Again, coordination between application replicas may be the solution to
        the problem. Each replica adds only a few connections to its pool so
        that they all have only 10 connections total. This won’t scale for more
        than 10 application replicas. Even with ten or fewer, how are they
        going to coordinate to know how many connections each one has and make
        sure each gets a fair proportion of the connections to use? When a
        replica shuts down, how do the others know so that they can start using
        its connections? Implementing a shared, distributed connection pool
        will not be easy.

        The solution is for the application to not implement a shared connection
        pool at all, much less one distributed across multiple replicas of the
        application. Rather, the application should use an integration solution
        to connect to the SoR and let it manage the connection pool. An
        integration solution such as

        IBM App Connect Enterprise or MuleSoft AnyPoint can manage connections
        to the SoR and be shared by multiple workload replicas.

        Figure 3-11 shows a Replicable Application that accesses an SoR. Rather
        than connect to it directly, the replicas share a connection pool
        managed by an integration service. The integration service enforces the
        constraints for connecting to the SoR, such as a limited pool of
        connections that it creates and shares. The workload replicas then
        share the integration service. Much like a database service coordinates
        multiple replicas accessing the same data, the integration service
        coordinates multiple replicas accessing the same SoR.



        Figure 3-11. Replicable Application with a connection pool
        """,
    "External Configuration":
        """
        External Configuration

        You are developing an application with a Cloud-Native

        Architecture . You want to be able to deploy the same

        Application Package to multiple environments without rebuilding it.

        How can I build my application once and yet be able to deploy it to
        multiple environments that are configured differently?

        An application is not deployed only once to a single environment; it is
        deployed multiple times to different environments. Each of these
        environments may be set up and operated differently, possibly requiring
        the application to work differently in each environment.

        Cloud Applications (Chapter 1) are portable, designed to run on whatever
        hardware is available. Developers should be able to deploy a Cloud
        Application to different environments as long as they are equivalent.
        One common environment is the developer’s local computer, where the
        developer may test out their latest changes. Other common environments
        are the stages in the software development lifecycle (SDLC) (such as

        dev , test , stage , and prod ), which are separate but

        equivalent environments. An enterprise may also encompass multiple
        production environments, perhaps for different geographies (such as
        north america and europe ) or different lines of business in the
        enterprise (such as

        marketing and accounts receivable ). Equivalency of

        these separate environments is the principle behind The

        Twelve-Factor App: X. Dev/prod parity . The application must be able to
        run equally well in any of these equivalent environments.

        While various environments are equivalent in many ways, they are not the
        same. A developer’s laptop is not running the same services as a cloud
        platform. The cloud environments for testing should include equivalent
        but separate service instances from those for production. For example,
        if the application requires a relational database with a particular
        schema, the database is provided as one installation on the developer’s
        laptop, another service instance is provided for testing environments
        full of fake test data, and at least one more service instance full of
        proprietary enterprise data is provided for production. The equivalent
        databases are hosted on separate network endpoints (e.g., IP address,
        domain, or URL) and certainly have different authentication
        credentials. These databases are equivalent, but because they’re
        separate servers, they’re accessed differently.

        An application has access only to the services in its environment. When
        the application is deployed to a development environment, it should
        have access only to the development database. Only when it is deployed
        to the production environment should it have access to the production
        database.

        The application should be built to be immutable. This is one of

        the principles behind The Twelve-Factor App: V. Build, release,

        run, as well as both a consequence and benefit of packaging an

        application as an application container image—such as a Docker image. An
        immutable application means that the exact same deployment artifacts
        are deployed into each environment. Deployment should not recompile or
        rebuild an application to deploy it into a new environment. When the
        application is immutable, the exact same artifacts that were used for
        testing are also deployed into production. Otherwise, if an application
        must be changed and rebuilt to deploy it into production, what’s
        running in production is not what was tested and approved in the
        testing environment.

        How can the same application use a different service instance (e.g., a
        different database) depending on the environment it’s deployed into?
        One approach is to hardcode literals for the service instance’s
        endpoint and credentials. But then every time the application is
        deployed into a new environment with a new service instance, the
        application’s code needs to be modified to change those literals, be
        recompiled, then retested. An immutable application cannot be modified
        and recompiled between environments.

        Another approach might be for the application to hardcode the endpoint
        and credential literals for all of the service instances in all of the
        environments. This assumes that the developers know all of the
        environments the application will ever be deployed into, that the
        service instances’ connection properties can never change, and that the
        developers should have access to all of these settings. That would mean
        giving developers access to the authentication credentials for the
        production services, settings that the production operations team
        should treat as a closely guarded secret. Even if this would work, the
        unchanged application has no way to know which environment it has been
        deployed into and therefore which set of literals to use.

        Another problem with hardcoding settings comes with committing code into
        the source code management (SCM) system. An SCM is widely shared with
        all developers who need access to the code. Environment settings should
        not be widely shared because anyone who knows the settings gains
        insight into how the enterprise’s internal environments are set up.
        Secret credentials should be even more closely guarded, not stored
        someplace widely shared.

        In traditional IT, a common approach to avoid hardcoding settings within
        an application is to store them in a properties file. That way,
        developers can change the settings by editing the file, and they do not
        have to recompile the rest of the application. However, this approach
        doesn’t work well in the cloud. A Cloud-Native Application is
        stateless, and a properties file is state (unless you are storing it in
        an external service like a secrets store). Even if properties are an
        exception, a cloud environment may not even have a file system to store
        the properties file into. Also, the properties file is deployed with
        the rest of the application, so the application still cannot deploy to
        multiple environments unchanged.

        Cloud Applications support Polyglot Development , where an application’s
        modules don’t all need to be developed in a single computer language.
        Settings need to be stored in a way that is language-independent, using
        an approach that will work for all languages and all environments,
        including cloud environments.

        Therefore,

        Store an application’s settings in an External Configuration separate
        from the application’s code so that the settings can be changed without
        changing the application artifacts.

        Configuration is typically stored in environment variables.

        An application accesses its configuration as an internal set of
        variables, populated from values that are stored externally. Because
        these configuration values are stored externally from the application,
        the values can be changed without having to change the application’s
        code and recompile it. An application can be deployed to different
        environments with different configurations without having to change the
        code, just change its set of External Configuration values in each
        environment.

        As shown in Figure 3-12, the application stores its configuration
        internally as variables and sets their values from a configuration that
        is stored externally.





        Figure 3-12. External Configuration

        The External Configuration values are typically stored in the OS

        as environment variables, as shown in Figure 3-13. Most include
        environment variables as a feature. Most programming languages have
        features for reading environment variables, so the program just needs
        to use those features. For each configuration variable the program
        needs to read, the program just needs to know the name of the
        corresponding environment variable.





        Figure 3-13. Environment variables

        As Figure 3-14 shows, configuration for the application is stored in
        environment variables in the OS’s environment. The deployment process,
        whether manual or automated, declares the environment variables and
        sets their values when it deploys the application into the OS. When the
        application runs in the OS, the program reads its configuration from
        the environment variables, optionally stores these values in its own
        internal variables, and uses the values as needed.





        Figure 3-14. External Configuration usage

        In this example, the configuration specifies the credentials to access
        and authenticate with an external MySQL database containing data for
        products. The deployer can set this configuration for one database in
        the development environment and a different database in production
        without having to change the program code, so the same Application
        Package can be deployed without modification in both environments.

        As explained in The Twelve-Factor App: III. Config:

        The twelve-factor app stores config in environment

        variables (often shortened to env vars or env). Env vars are

        easy to change between deploys without changing any code;

        unlike config files, there is little chance of them being

        checked into the code repo accidentally; and unlike custom

        config files, or other config mechanisms such as Java System

        Properties, they are a language- and OS-agnostic standard.

        Environment variables are a very good place to store the configuration
        settings for an application. They are not specific to any one language
        or OS. Unlike a properties file, environment variables do not require a
        local file system. If needed, each variable can be shared by multiple
        applications, as long as that doesn’t create an unnatural coupling
        between the applications. If multiple applications always need the same
        setting, such as sharing the same database, they should share a single
        environment variable. If they may eventually need different settings,
        such as each using its own database, they should use separate
        environment variables that may or may not contain the same value.

        Application settings may include private data such as credentials that
        should not be stored in a public SCM. Whereas properties files may
        accidentally get checked into an SCM, environment variables will not.

        While storing an application’s configuration in the OS’s environment
        solves many issues, setting an environment’s variables can be a
        chicken-and-egg problem. As part of the deployment process, something
        must set the environment’s variables with the configuration settings,
        which must be set before the application is deployed into an
        environment.

        An easy way to initialize the environment variables is to store the
        settings in a properties file that a deployment script can use to set
        the variables before deploying that app. The environment variables
        decouple the application from how the values are stored—only the
        deployment process needs access to the properties file and the file
        system. If the values are stored in a properties file, that file
        shouldn’t be checked into SCM. Settings can also be stored in two
        files, sensitive and nonsensitive, where only the nonsensitive file is
        checked into SCM. The sensitive settings should be stored in a secrets
        vault.

        Rather than storing the External Configuration in environment variables,
        it is sometimes stored in a database. While convenient, this approach
        requires that the application have access to a database, an extra
        middleware service that is not built into an OS like environment
        variables but one that most applications are likely to need anyway.
        This database approach also creates its own chicken-and-egg problem for
        initializing the application: the application needs settings for
        accessing the database that contains the settings.

        Environment variables are often populated from a values management
        service provided by the platform—such as HashiCorp Vault, Parameter
        Store on Amazon Web Services (AWS), and Secrets Manager on IBM Cloud.
        An application can access such a service directly via an API, bypassing
        environment variables. However, that approach makes the application
        directly dependent on the service, with all of the problems of making
        the application directly dependent on a database of values.
        Furthermore, each service has its own API, locking in the application
        so that its code works only on the platform with that service.
        Environment variables avoid this lock-in by separating how the
        application accesses the values from how the values are populated,
        enabling the deployment process to easily switch between different
        storage methods without needing to modify the application, and without
        making the application dependent on the storage method.

        Externalizing an application’s configuration into environment variables
        makes the settings part of the environment the application is deployed
        into. Each environment independently sets the variables for its
        configuration. The application is able to run unchanged in multiple
        environments and use a different configuration in each environment.
        Cloud environments and their OSs support storing environment variables,
        and modern programming languages support reading environment variables.
        Unlike with a properties file, environment variables do not require a
        file system and cannot accidentally get checked into an SCM.

        When an application externalizes its configuration as a set of
        environment variables, the cloud environment must provide a way to set
        environment variable values when running the application. Each platform
        handles that differently. Setting these environment variables’ values
        can be a chicken-and-egg problem. The configuration for the code that
        initializes the variables should not be checked into SCM, and
        credentials should be stored in a secrets vault. Thus, many cloud
        platforms

        provide some sort of Configuration Database to solve this problem for
        applications running on their platform.

        When the application is a Replicable Application , the platform sets the
        environment once so that all of the replicas share the same
        configuration.

        Externalizing your configuration enables other design principles. For
        example, a developer may choose to test locally with a local copy of a
        database like Postgres and then connect to an AWS or Azure database
        service when testing in the cloud. This toggling of features and
        environment-specific configuration choice is critical when testing
        applications built

        using a Microservices Architecture (Chapter 4). Each component can be
        tested individually and integrated within the system before testing,
        rather than always having to test a component with all of its
        dependencies—which can lead to having to test an entire system just to
        test one component in the system.

        Examples

        Application languages that support deployment techniques like
        application packaging also support accessing environment variables.
        Likewise, cloud technologies like containers and container
        orchestrators provide features for setting environment variables. Cloud
        platforms provide services for storing credentials securely and making
        them available to applications by setting them in environment
        variables.

        Read environment variables in Java

        As Oracle documents in Environment Variables, a Java application can
        read environment variables using the

        System.getenv static methods.

        An application can read all of its environment’s variables into a

        Map , as shown in Example 3-12.

        Example 3-12. Java code for reading all of an environment’s variables

        Map env = System.getenv(); for (String envName : env.keySet()) {

        System.out.format("%s=%s%n", envName, env.get

        }



        An application can also read an individual environment

        variable’s value by specifying its name, as shown in Example 3-

        13.

        Example 3-13. Java code for reading one of an environment’s variables

        String name = "PORT";

        String value = System.getenv(name);

        if (value != null) {

        System.out.format("%s=%s%n", name, value);

        } else {

        System.out.format("%s is" + " not assigned.%n

        }



        A deployment tool that the Java application doesn’t even know about can
        set the values of environment variables, and the application can read
        them simply by knowing the variables’ names. This works on a range of
        platforms and helps keep the application platform-independent.

        Read environment variables in Node.js

        A Node.js process makes all environment variables accessible

        using a global env process object. Example 3-14 shows how an application
        can read all of its environment’s variables from this object.

        Example 3-14. Node.js code for reading all of an environment’s
        variables

        const process = require('process'); var env = process.env;

        for (var key in env) {

        console.log(key + ":\t\t\t" + env[key]);

        }



        An application can also read an individual environment

        variable’s value by specifying its name, as shown in Example 3-

        15.

        Example 3-15. Node.js code for reading one of an environment’s
        variables

        const app = require('http').createServer((req, re const PORT =
        process.env.PORT || 3000;

        app.listen(PORT, () => {

        console.log(`Server is listening on port ${PORT });



        A deployment tool that sets the values of environment variables and the
        application that reads them do not need to know about each other. The
        setter doesn’t need to know the language used to implement the
        application—Java, Node.js, or another—only that the application is able
        to read environment variables. Docker container environment variables

        Like application programs and packages, container images should also be
        built with an External Configuration so that their containers can be
        deployed to a number of environments. The running container will read
        the environment variables and make them available to its processes. For
        example, when

        running a container using Docker , use -e flags in the docker run
        command to specify environment variable settings.

        Kubernetes Configuration Map and Secret

        Kubernetes, a popular container orchestrator, enables an application to
        access settings as environment variables using

        two features: ConfigMap and Secret. Both a configuration map and a
        secret store a set of data as key-value pairs. The data in a
        configuration map is stored as plain text and so should not be
        confidential. The data stored in a secret is encoded and so can be as
        confidential as the encoding method.

        For example, the YAML code in Example 3-16 creates a ConfigMap named
        game-demo that sets the values for two properties.

        Example 3-16. Kubernetes configuration map

        apiVersion: v1

        kind: ConfigMap

        metadata:

        name: game-demo

        data:

        # property-like keys; each key maps to a simple
          player_initial_lives: "3"

        ui_properties_file_name: "user-interface.prope



        An application in a pod that reads this configuration map has access to
        those two values named player_initial_lives and
        ui_properties_file_name .

        The YAML code in Example 3-17 creates a Secret named

        mysecret that sets the values for two properties.

        Example 3-17. Kubernetes Secret

        apiVersion: v1

        kind: Secret

        metadata:

        name: mysecret

        type: Opaque

        data:

        USER_NAME: YWRtaW4=

        PASSWORD: MWYyZDFlMmU2N2Rm

        An application in a pod that reads this secret has access to the plain
        text data for the values named USER_NAME and

        PASSWORD .

        Secrets storage and encryption

        An enterprise should store the sensitive settings in a secrets

        vault such as HashiCorp Vault, or better yet a hardware security module
        (HSM) that only the enterprise can access. If sensitive settings must
        be stored in SCM, they should be encrypted using

        tools like git-crypt.

        AWS Systems Manager Parameter Store and AppConfig

        AWS Systems Manager Parameter Store stores configuration data and
        secrets. This data can be accessed in compute services such as Amazon
        Elastic Compute Cloud (Amazon EC2), Amazon Elastic Container Service
        (Amazon ECS), and AWS Lambda. A feature within AWS System Manager, AWS
        AppConfig, allows users to store and manage custom application
        configuration from within application programs.

        IBM Cloud Secrets Manager

        IBM Cloud Secrets Manager—built on HashiCorp Vault—stores configuration
        settings that should not be stored in source code management. It
        manages their lifecycle, controls access to them, records their usage
        history, and optionally encrypts them with user-provided keys. It can
        also be configured to create Kubernetes secrets, and those secrets can
        be encrypted with user-provided keys. Applications can use these
        secrets to authenticate to databases and storage, and continuous
        delivery services can use them to gain access to deployment
        environments.
        """,
    "Backend Service":
        """
        Backend Service

        You are developing an application with a Cloud-Native

        Architecture . The application implements custom business

        logic that deploys as an Application Package . The application needs
        some functionality that is common among many applications—such as data
        persistence or messaging.

        How can multiple applications share the same reusable functionality?

        A common approach in traditional IT to make functionality reusable has
        been to implement it as a reusable code library. Any application that
        needed the functionality would compile and link in the library as part
        of its executable process. For example, a Java program can include
        separate JAR files, Node.js programs can include modules, and a C#
        program can use the .NET libraries.

        The library approach has several limitations:

        Language

        An application implemented in a particular language can typically only
        use libraries written in the same language.

        Distribution

        The libraries are part of the application process and therefore can only
        run on the same computer as the rest of the application.

        Scalability

        The library scales with the application process. The library cannot
        scale independently of the rest of the application.

        Failure

        If the library fails, it causes the rest of the application to fail,
        perhaps causing the entire application process to crash.

        Composable

        To reuse multiple libraries, an application must be able to include them
        all in its process. This can be a problem for libraries unless they
        were designed to work together.

        Duplication

        Multiple applications that embed the same library each load their own
        copy, causing bloat that limits scalability.

        Traditional IT applications typically run in middleware servers that
        provide capabilities like automating business processes, running rules,
        and queuing messages. Middleware that also hosts the application is
        essentially a giant code library, with the same code library
        limitations.

        The cloud needs to be able to vary the application independently of code
        libraries.

        Therefore,

        A Cloud-Native Application should connect to reusable functionality
        remotely as a Backend Service. The service can be stateful, reused by
        multiple applications, and managed by the cloud platform.

        A single Cloud-Native Application can delegate to multiple Backend
        Services. A single Backend Service can be used by multiple
        applications.

        As shown in Figure 3-15, a Cloud Application can delegate to several
        Backend Services, such as a database, a messaging system, and a process
        automation engine. Many cloud platforms include a catalog of services
        hosted as SaaS that applications can reuse as Backend Services. Many
        Backend Services perform the sort of functionality provided by
        middleware servers on traditional IT.





        Figure 3-15. Backend Services While Cloud Applications can embed
        reusable code libraries the way a traditional IT application can, they
        gain even greater flexibility by being able to connect to Backend
        Services remotely. A Cloud Application can even reuse other
        applications by treating them as Backend Services.

        In cloud, reusing code libraries as a Backend Service overcomes the
        limitations of a library:

        Language

        The application and the service can be implemented in different
        languages and technologies.

        Distribution

        The application and the service run in different processes, so they can
        run on the same computer or on separate computers.

        Scalability

        The application and the service run in different processes, so they can
        scale independently.

        Failure

        The application and the service run in different processes, so a failure
        that crashes one does not crash the other.

        Composable

        An application can connect to multiple services and combine their
        functionality.

        Duplication

        Multiple applications that reuse the same service share a single copy,
        thereby consuming just one set of capacity.

        The role of a Backend Service is distinct from that of the application
        program. Backend Services are specialized for reusable application
        functionality, whereas an application’s program is specialized for the
        business logic that implements a particular set of user requirements. A
        Backend Service performs a single capability that many applications
        need, such as data persistence, messaging, rules processing, or event
        processing. Whereas business logic is often industry-specific and gives
        an enterprise competitive advantage, Backend Services are usually
        industry-neutral. The Backend Service does not give an enterprise
        competitive advantage as is; the advantage to the enterprise is in how
        they use the service and the fact that they could buy the service
        rather than build it themselves. An application program typically runs
        on behalf of a single enterprise, whereas a Backend Service is
        typically used by multiple enterprises while enabling an enterprise to
        isolate its usage by creating its own instance of the service.

        As explained in The Twelve-Factor App: IV. Backing services:

        A backing service is any service the app consumes over the

        network as part of its normal operation… .Backing services

        like the database are traditionally managed by the same

        systems administrators who deploy the app’s runtime. In

        addition to these locally-managed services, the app may also

        have services provided and managed by third parties.

        The Backend Service paradigm works so well that cloud platforms tend to
        make all functionality into services, yet some of the services in a
        service catalog are more backend than others. The services in a catalog
        come in two broad varieties:

        Application service

        The application connects directly to the service as a Backend Service.
        Its implementation includes client code that invokes the service’s API,
        such that the service is required for the application to work. For
        example, for an application to work with a database or a messaging
        system, it must be written to do so.

        Platform service

        The cloud platform environment is configured to include the application
        and services that enhance how it runs. The application does not depend
        on these services directly— they are optional. For example, an
        application usually does not interact with a key vault directly; the
        database does. Observability services can be added to the environment
        and gather information about the application without changing the
        application.

        The concept of Backend Service existed before the cloud. Even in
        traditional IT, most databases and messaging systems run in separate
        servers that applications connect to remotely. The cloud takes this to
        an extreme, whereby a program is only the code implemented by the
        development team and perhaps some embedded code libraries, and
        everything else in the application is Backend Services the program
        connects to remotely.

        Backend Services can be developed by third-party vendors so that
        application developers can focus on the user functionality that makes
        their application unique. Many cloud platforms provide a catalog of
        Backend Services, available for applications deployed on that platform
        to use. Many software vendors make their products available as SaaS
        that applications can use as Backend Services. OperatorHub.io and Red
        Hat Marketplace make libraries of Kubernetes operators available, which
        can be installed in application environments so that applications can
        use them as Backend Services.



        A single application can delegate to multiple Backend Services, and a
        Backend Service can be shared by multiple applications. Each Backend
        Service can be written in a different language and used by applications
        written in different languages. An application and its Backend Service
        can run on different computers, and they are able to scale
        independently. Each Backend Service focuses on a specific set of
        functionality that is highly reusable by multiple applications.
        Applications can connect to application services directly and
        indirectly make use of platform services embedded in the cloud
        platform. Backend Services can be developed by third-party vendors and
        made available built into a cloud platform in a service catalog.

        However, Backend Services can complicate an application architecture.
        The application must be able to access the service remotely via a
        network connection, which can be slow and unreliable. It is not always
        clear where and how a Backend Service is hosted, which can be a
        challenge for applications with data sovereignty restrictions. It is
        not always clear whether a Backend Service is single-tenant or
        multitenant, and how multiple tenants are isolated. A Backend Service’s
        reliability can be lower than an application requires, effectively
        lowering the application’s reliability. Each Backend Service should
        include a user agreement that stipulates its service-level agreements
        (SLAs), which the application developer must confirm are compatible
        with their application’s requirements.

        If an application is designed as a Replicable Application , all of its
        replicas will share the same Backend Services. These shared services
        help the otherwise unrelated replicas coordinate to act like one big
        application.

        Any Cloud Database can be a Backend Service, as long as it runs in a
        separate process from the application. Some databases can be embedded
        within an application: Apache Derby in Java programs, SQLite as a C
        library, eXtremeDB for C and C++ programs. When embedded, a database is
        not a backend system. When the database server runs independently of
        the application and can be shared by multiple applications, Cloud
        Applications use it as a Backend Service.

        A Backend Service is part of a Distributed Architecture that can

        be implemented as a Microservices Architecture (Chapter 4).

        An Event Backbone is a Backend Service. It connects event consumers to
        event producers, all of which use it as a shared Backend Service.

        Examples

        A compelling advantage of many public cloud platforms is that the
        platform is chock full of Backend Services. These services are designed
        for applications to use as Backend Services or otherwise to add
        capabilities to an application that the development team doesn’t have
        to implement itself. Infrastructure-as-a-Service (IaaS) and
        Platform-as-a-Service (PaaS) services such as virtual servers and
        container orchestrators host applications but are not Backend Services
        for applications. An application can connect directly to application
        services, which are SaaS services for adding functionality to the
        application, such as data persistence, caching, messaging, and process
        automation. An application’s environment can be configured to include
        platform services that the application doesn’t connect to directly,
        such as API gateways, authentication, key management, monitoring, and
        log aggregation.

        Database services (application service)

        A Cloud-Native Application runs as a Stateless Application . A problem
        with making an application stateless is that most applications have
        state, so where does the state go? It goes in databases and other data
        stores, which the application uses as Backend Services. The database
        server runs as a service, available for any client application that
        wants to use it to create a database and store data. Cloud platforms
        provide numerous

        different Cloud-Native Storage (Chapter 7) services.

        Examples of database Backend Services include Amazon Relational Database
        Service (Amazon RDS) and Amazon DocumentDB, Azure Cosmos DB
        (document) and Azure Cache for Redis (key/value), and IBM Db2 on Cloud
        (relational) and IBM Cloudant (document). Object storage services—such
        as Amazon Simple Storage Service (Amazon S3), Azure Storage, and IBM
        Cloud Object Storage—are also Backend Services.

        Integration services (application service)

        Messaging services connect applications; each application connects to a
        messaging service as a Backend Service. Examples include Kafka, Amazon
        Managed Streaming for Apache Kafka (MSK), Azure Event Hubs, and IBM
        Event Streams; IBM MQ on Cloud, Azure Service Bus, Amazon MQ, RabbitMQ,
        and Apache ActiveMQ; and IBM App Connect on IBM Cloud.

        An API gateway exposes internal application APIs as external endpoints
        and can authorize their use. An application doesn’t try to manage this
        itself. The gateway runs as a service, but rather than connect to the
        gateway as a Backend Service, the deployment process publishes the
        application’s APIs as endpoints in the gateway. Examples include Amazon
        API Gateway, Azure API Management, and IBM API Connect.

        Security services (platform service)

        A key management service (KMS) or a key vault that stores cryptographic
        keys securely is a Backend Service. Keys are stored in the KMS for safe
        keeping. When a database or storage service needs a key, it retrieves
        it from the KMS. Examples include Azure Key Vault Managed Hardware
        Security Module (HSM), AWS Key Management Service (AWS KMS), and IBM
        Cloud Hyper Protect Crypto Services.

        External Configuration talks about storing secrets in a secrets vault.
        Like a key vault, a secrets vault is typically hosted as a Backend
        Service. The application may interact with the secrets vault directly,
        making it an application service. Or the application may be able to
        interact with the secrets vault indirectly, such as by sharing
        Kubernetes secrets, making it a platform service.

        A user authentication service enables the user to log in to the
        application. Rather than the application implementing this
        functionality itself, multiple applications can all share a service
        that sits in front of the applications and authenticates users on
        behalf of the applications. Examples include IBM Cloud App ID and Azure
        Front Door.

        Observability services (platform service)

        Monitoring services and log aggregators gather events from applications
        while they are running to display to the operations staff. Rather than
        each application performing this functions itself, separate services
        perform this work. The application may not even know these services are
        connected to it. Examples include Prometheus for monitoring and Fluentd
        for log aggregation.
        """,
    "Cloud Database":
        """
        Cloud Database

        You’re developing an application with a Cloud-Native

        Architecture that has domain data and needs to persist it.

        Perhaps you’re developing a Self-Managed Data Store for a

        Microservice .

        How should a cloud-native application store data persistently in a cloud environment?

        As discussed in Stateless Application , applications manage two types of state: session state and domain state. A database of record is storage for the most reliable copy of the domain state.

        Where should an application store its domain state? An application needs to persist its domain state so that the data can be recovered after a crash and shared among replicas of the application, users of the application, and other applications. Raw storage—such as block, file, and object storage—seems like a tempting place, and that is ultimately the infrastructure where data is persisted. But storage presents two challenges for applications that need to persist and access their domain state:

        Concurrency

        Storage can easily manage data when there’s only one application client thread at a time reading or writing. But when one thread tries to read data while another is updating it, applications can retrieve inconsistent data from storage. If two threads try to write data at the same time, it’s possible to overwrite or corrupt the data in storage. Even if a Microservice is the only application

        accessing the data in its Self-Managed Data Store , concurrency still occurs between the Microservice’s

        replicas (see Replicable Application ) that share the data store.

        Querying

        Storage works well when an application knows what data is stored and what data it wants and can specify where in the storage to find that data. But if an application needs to perform a search, all it can do is read all of the storage and filter for the data it wants, which is terribly inefficient, especially as data sets grow in size.

        Databases, such as the Relational Databases in traditional IT, help applications manage storage. However traditional enterprise databases may not fit the cloud well in three respects:

        Schema

        Traditional databases force data into a common schema, thereby telling the application how to structure its own data. Applications have to accommodate the database, with many applications having to implement complex object-relational mapping just to make their Domain

        Model (Patterns of Enterprise Application Architecture,

        2002) (see Domain Microservice ) fit the database schema. An application with data that doesn’t follow a strict structure will have difficulty mapping it to a fixed schema database.

        Storage minimization

        An enterprise database strives to write as much data as possible into as little storage as possible. Such databases typically update records in place, which uses storage more efficiently but requires aggressive use of locking, hurting the performance of concurrent threads and lowering the database’s overall throughput and scalability.

        Single process

        Enterprise databases often run as a single active process that scales vertically but not horizontally and so is a single point of failure.

        Cloud-native changes the architecture of an application so that it works better in the cloud. Likewise, databases need a new architecture so that they work better in the cloud.

        Therefore,

        Persist the data for a Cloud Application in a Cloud Database, one that scales horizontally as Cloud Applications do and offers the application flexibility in how it stores and accesses the data.

        A Cloud Database works well hosted in the cloud and stores the

        state for a stateless Cloud-Native Application (Chapter 3), as

        shown in Figure 7-7.





        Figure 7-7. Cloud Database



        A Cloud Database is much like a traditional IT database in that it is responsible for storing and managing data, handling much of these responsibilities so that the application doesn’t have to. A Cloud Database differs from its traditional IT counterpart in that it is able to run reliably on a cloud’s unreliable hardware, can easily accommodate a range of topologies, and stores data in the way that applications model domains.

        Databases organize data into records that can be stored anywhere on the disk, simplifying an application to work with records as units of data and not needing to know where and how the records are stored. Databases must be designed to do the following well:

        Concurrency

        A database isolates threads to keep the data consistent. A database will not allow two applications to write to the same record at the same time, and when one application thread is writing a record, a database will not allow any other thread to read that data. A database caches data so that multiple read threads for the same data access only the disk once and organizes the records on the disk to avoid thrashing. Without a database, all of the applications are responsible for coordinating all of their threads to avoid conflicts.

        Querying

        A database separates the identity of a record from where it is stored on disk, understands the records’ structure to know which ones have the data an application is searching for, can index the structure to find records more easily, and can navigate between related records. Without a database, this functionality becomes each application’s responsibility.

        Whereas enterprise databases are designed to accommodate data, Cloud Databases are designed to accommodate Cloud Applications in the following ways:

        Schema

        Whereas an enterprise database has a one-size-fits-all approach that tells the application how the data will be stored, an application tells a Cloud Database how to store the data. Many Cloud Databases are schemaless, able to store an application’s state the way it’s stored in the domain model. This makes the state easier and faster to store and retrieve, and facilitates managing not only well-structured data but also data that is semi-structured and unstructured, as well as data representing networks of connected records.

        Data access

        Whereas an enterprise database will excel at storing maximum data in minimum disk space, as disk has become cheaper, Cloud Databases have focused on enabling data access to meet the flexibility and availability of cloud environments, simplifying data access for applications and maximizing concurrency and throughput.

        Multiple, horizontally scalable processes

        Whereas an enterprise database often runs in a single active process, a Cloud Database runs in multiple replica processes that can scale horizontally to work the way the cloud works. It also replicates the data to keep it available even when a database process becomes unavailable. A database may have difficulty updating multiple distributed copies of a record concurrently. Replicated Databases tend to rely on eventual consistency, where each copy of a record receives an update over time.

        A Cloud Database manages storage better than an application accessing storage directly, works more like how the application works, and works more the way the cloud works.



        Cloud Databases work the way the cloud does and the way applications do and reduce the effort applications need to manage data persistence.

        Because most Cloud Databases work differently than the Relational Databases most traditional IT developers are accustomed to, the developers need to learn new databases and new approaches to persisting and accessing data. Eventual consistency can be a challenge since application design tends to assume a single version of the truth.

        There are many Cloud Databases to choose from. The best database for a Cloud Application’s requirements depends on three criteria:

        Replication

        A Replicated Database runs multiple server processes for accessing the same data. With these processes, the database comprises horizontally scalable redundant units,

        much like a Replicable Application .

        Redundant data storage

        A database running process replicas often also replicates its data, storing copies of a record in multiple processes, both to reduce single points of failure and to improve

        read throughput. The section “Database Topology and

        Database Selection” has a detailed discussion of how this is accomplished across various database implementations.

        Data structure

        An Application Database enables applications to persist data and access it in a way that is appropriate to a particular application’s data structures and algorithms.

        In addition to application databases, cloud platforms also host

        Configuration Databases , which cloud platforms and services use to manage highly concurrent shared configurations.

        Just as an application monolith can be refactored into

        Microservices , a large set of data (such as an existing enterprise database of record) should be refactored into

        separate modules. A Data Module stores each independent set of data in a separate logical database. Multiple databases can be hosted in the same database server or in separate database

        servers. Database-as-a-Service (DBaaS) makes it easy to create and manage multiple database server instances to manage multiple Data Modules. A single DBaaS server can store multiple Data Modules that are designed for the same type of Cloud Database.

        Multiple Data Modules enables the opportunity for Polyglot

        Persistence , which allows for resolving these three criteria differently for different sets of data. Since each application module or Microservice maps to its own Data Module, which is stored in a separate logical database, each database can easily be of a different type, making the overall application’s persistence polyglot.

        Often a key set of data needs to be queried extensively while it is also being updated frequently, which makes the database a significant performance bottleneck, even a Cloud Database. The

        Command Query Responsibility Segregation (CQRS) pattern helps resolve this problem.

        Examples

        With a range of database services to choose from with different capabilities, Cloud Applications do not all need to use a single enterprise database.

        Several NoSQL databases work like cloud services whether deployed on traditional IT or on a cloud platform, including

        Apache CouchDB, MongoDB, Apache Cassandra, Redis, and

        Neo4j Graph Database.

        Most cloud platforms include several Cloud Database services:

        Amazon Web Services (AWS)

        Hosts several DBaaS services, including Amazon Aurora,

        Amazon DynamoDB, Amazon ElastiCache, Amazon

        DocumentDB, and Amazon Neptune

        Microsoft Azure

        Hosts databases such as Azure SQL Database, Azure

        Database for PostgreSQL, Azure Cosmos DB, and Azure

        Cache for Redis

        Google Cloud databases

        Include Cloud SQL, AlloyDB for PostgreSQL, Bigtable,

        Firestore, Memorystore, and MongoDB Atlas

        IBM Cloud

        Hosts a number of DBaaS services, such as IBM Db2 on

        Cloud, IBM Cloud Databases for EnterpriseDB, IBM Cloud

        Databases for PostgreSQL, IBM Cloudant, IBM Cloud

        Databases for MongoDB, and IBM Cloud Databases for

        Redis

        These Cloud Databases implement a number of the different patterns, which we will see later in this chapter.
        """,
    "Replicated Database":
        """
        Replicated Database

        (aka Distributed Data Store)

        You are building an application following a Cloud-Native

        Architecture and are in the process of choosing a Cloud

        Database . For your application to be highly available, its database also needs to be highly available.

        How can a Cloud Database provide the same quality of service as a cloud-native application, with the same availability, scalability, and performance as the application?

        For a Cloud-Native Application (Chapter 3) to work well in the

        cloud, all of the Backend Services it depends on also need to work well in the cloud. An application is only as reliable as its Backend Services. The single most important Backend Service for many applications is its database, which is key to implementing most of an application’s functionality. For an application to be highly available, its database must also be highly available.

        A common approach to make a database highly available on traditional IT is for it to run in two processes, one active and one standby. The clients use the first process to access data. If the first process fails, the database makes the second process active, and the clients switch over to use it to access data.

        This active-standby approach has limitations. If the processes share storage and that fails, both processes become useless. Therefore, each process needs its own storage, which means that every time the first process updates its data, the second process needs to copy the update and do so with zero latency between the processes to avoid any data loss in an outage. A detail that simplifies keeping both copies synchronized is that changes occur only in the active copy, so copying data is performed in a single direction, from active to standby.

        Even with redundant storage, other problems remain. Switching the clients from the first process to the second process takes time, during which the clients experience an outage. If the second process also fails before the first process recovers, the clients experience a prolonged outage until one of the processes can recover. By cloud standards of always-on availability, active-standby is a less-than-perfect solution.

        The unreliable nature of cloud infrastructure is especially problematic for the active-standby approach. Failover from active to standby because of infrastructure failure is no longer an unusual occurrence caused by a major outage; it can occur frequently on the cloud simply as part of frequent routine maintenance. Database clients can experience frequent outages because of frequent failover. Active-standby has no way to avoid this problem other than wishing the active process could run as reliably on cloud infrastructure as it does on traditional IT, which it cannot.

        A cloud-native application is able to scale elastically, which helps it maintain steady performance, using more capacity when client load increases and releasing capacity when the client load decreases. The active-standby approach has just one active process, which has limits on how much client load it can handle from its applications. An active process can grow bigger when the load increases, but only until its server runs out of capacity. And it usually cannot grow smaller when load decreases. Even if the active process can grow large enough, network I/O may become a bottleneck, throttling numerous database clients accessing data through a single process.

        For a database to scale, not only does the server process need to scale, but the storage needs to scale as well. Just as a process cannot grow once it has used all of the capacity of its server, the database’s data cannot grow once it has used all of the capacity of its storage. Even if the storage capacity is huge, the active process has limits as to how much storage it can manage effectively. A single process accessing huge amounts of data will eventually be throttled by storage I/O.

        For a database to be as scalable and reliable as its cloud-native application, it needs an architecture that scales better than active-standby.

        Therefore,

        Select a Replicated Database, one that runs multiple active server processes for accessing the same data, that stores multiple copies of the same data, and that applies updates to the data consistently across the copies.

        A Replicated Database runs not as a single server process but as a cluster of nodes, each of which is a database server process

        with its own storage, as shown in Figure 7-8. The database coordinates these nodes so that they work like one large database server process. Clients access the database as though it

        runs in a single process (as was shown in Figure 7-7).





        Figure 7-8. Replicated Database

        The nodes in a Replicated Database’s cluster can all run on a single computer but can also be distributed across multiple computers. Each node has its own storage, either local to the computer hosting the node or accessible from the node’s computer. The database stores its data redundantly by replicating copies across the nodes, making the data highly available using commodity storage, thereby eliminating the need for specialized high-availability storage such as a RAID array.

        A Replicated Database works much like a Replicable Application , if the application were stateful and each replica also had storage. A Replicated Database scales by adding nodes. While some of the nodes can run in standby mode, the database has multiple active nodes capable of serving client requests, thereby distributing client requests across multiple nodes.

        The Replicated Database’s architecture makes the database more reliable and increases the data availability, improves the scalability of client I/O, and enables the storage to grow to store more data while also improving storage I/O performance. The database runs reliably on unreliable cloud infrastructure because when a node and its storage become unavailable, clients are still able to access the node’s data using other nodes and their storage. A more reliable database improves the availability of its data. When too many clients become a bottleneck for accessing data, the database scales to run more nodes on more computers with more network connections and bandwidth. When storage I/O becomes a bottleneck, by scaling to run more nodes with more storage, the database scales to lower each node’s storage I/O demands.

        Replicating across multiple nodes with redundant copies of the data works really well for read-only data, but becomes a challenge for updating data. Whenever a client creates or updates data, the database synchronizes its replicas. Because each data record is stored redundantly in multiple nodes, when a client updates a data record, synchronization duplicates that update on each copy of the record. While the database is updating multiple copies, those copies can become temporarily inconsistent for clients reading that record.

        While a single database server can keep its data always consistent, a data record in a Replicated Database can become inconsistent temporarily while the database synchronizes an update. A single database server keeps its data immediately consistent by locking one or more records while it updates them. For a Replicated Database to lock a set of records, it needs to establish a distributed lock across all of the nodes that store copies of the records.

        While some Replicated Database implementations do support distributed locking, its complexity lowers the database’s reliability and performance. To avoid that complexity, the preferred configuration achieves eventual consistency, often by employing multiversion concurrency control (MVCC)

        (Transactional Information Systems, 2001) so that each replica can update at its own pace and clients can read the records while they are being updated. Eventual consistency enables a distributed database to maintain availability with good performance. This advantage becomes most evident when a node is unavailable and cannot be updated. Rather than blocking the whole database and all of its clients while it waits for all nodes to be available, the database keeps operating without the missing node by using the other nodes and their redundant copies of the data. When the unavailable node rejoins the cluster, the database restores the node by performing the data updates that it missed, thereby reestablishing its consistency with the rest of the cluster.

        During eventual consistency, while the database is updating each copy of a data record individually, different clients reading the record may see different versions of the data. During synchronization, clients reading the same logical record from different nodes will each see a consistent version of the data, but they may be different versions of the data. Effectively, some clients see the newly updated data, while others still see the old data before it has been updated. Eventually, often in a matter of milliseconds when the cluster is stable, the database will update all of the copies and all clients will see the updated data. Another source of inconsistency can occur in a Replicated Database when two clients update different copies of the same record. When two clients make two different changes to two different copies of the same data, the result is a conflict that the database will log as an error to be resolved manually.

        To simplify synchronizing updates across replicas and avoid deadlock and write conflicts, many Replicated Databases store their data differently than a traditional Relational Database does. A Relational Database often normalizes the data for a single entity across multiple tables, optimizing storage efficiency and enforcing consistency within shared data. Conversely, many replicated databases avoid normalizing the data by storing each logical entity as a single record. A replicated database can synchronize updates to a single record more easily, improving performance and reliability and shortening the time that the replicas are inconsistent, thereby avoiding conflicts. Data in a single record is not only easier for the database to manage, but it also simplifies client access to the data and improves throughput to the client.

        A Replicated Database has higher availability because its servers and its data are replicated, yet the relationship between the replicas affects how well the replication works. There are two main replication models, which differ in the relationships between the replicas: leader-follower (formerly known as master-slave, aka primary-secondary) and quorum-based consensus. The leader-follower model is simpler because one node is in charge but becomes a problem when the leader becomes unavailable. Without a node that’s in charge, the followers don’t know what to do, and the cluster stops working until it can either reestablish communication with the leader or identify a new leader. With the quorum-based model, all of the cluster members are equal, so as long as two out of three of the members are working, they can agree on what to do and the cluster keeps working. The leader can become a bottleneck and a single point of failure. A quorum-based cluster can avoid single points of failure by distributing members across anything that can fail, such as multiple computers in multiple data centers in multiple regions.

        Replication as a pattern is a basic requirement for a cloud-scale database. However, there are multiple different topologies that can support data replication. These include both solutions that use a leader-follower approach and those that use a clustering

        approach. The section “Database Topology and Database

        Selection” explains the different potential topologies, but the key is that whichever solution you choose must have a topology that supports both the replication of the data and the process for accessing the data. In the end, this decision is internal to the database and hidden from the application, and therefore not a decision for you to make.

        A Replicated Database scales the way a Cloud-Native Application scales, making the database as scalable and reliable as the application. It makes the data highly available on unreliable cloud infrastructure and maintains performance even as the size of the data set and client load increase.

        To maintain reliability and performance, a Replicated Database avoids distributed locks and instead employs eventual consistency, which increases availability but means clients may temporarily see old data in some replicas that has already been updated in other replicas. To make synchronization more reliable, Replicated Databases often store all of the data for an entity in a single unnormalized record. However, that single record is often also easier for an application to use. Some replicated databases use different replication strategies than others, which can affect how well the database works in a distributed outage.

        The architecture for a Replicated Database is similar to that of a

        Replicable Application . Just as the application can scale by running in more replicas, which also makes the application more reliable, a Replicated Database runs more nodes to increase its scale and reliability.

        To maintain immediate consistency, a Replicated Database would need to establish a distributed lock so that it can update

        all of the copies of a record in a distributed transaction. Service

        Orchestrator explains the complexity of distributed transactions, especially in a cloud’s unreliable infrastructure, and why they should be avoided.

        Replicated Databases are used for two purposes, Configuration

        Databases and Application Databases . Different types of Application Databases store data records in different formats to

        facilitate different usages. Polyglot Persistence enables different

        Data Modules to be stored in different types of databases.

        The database provided by a Database-as-a-Service is often a

        Replicated Database, making it a perfect Backend Service to provide persistence or caching for a Cloud-Native Application.

        Examples

        Most NoSQL databases are replicated. Let’s consider three of the most popular ones: MongoDB, Redis, and CouchDB. Each runs in a cluster of multiple nodes that can be distributed across multiple computers, and each database’s cluster can remain functional even when some nodes fail, enabling these databases to run reliably on unreliable cloud infrastructure. However, each one has a different cluster architecture that makes some more resilient than others.

        MongoDB

        A MongoDB cluster, as shown in Figure 7-9, consists of a set of data baring nodes with exactly one primary node and multiple secondary nodes. On a cloud platform, each node can run on a different computer, thereby distributing the set across computers and making the database run more reliably on unreliable infrastructure.

        The cluster synchronizes the data throughout the nodes in the set. The primary node replicates data updates to the secondary nodes asynchronously, keeping their data in sync. Because the data in the secondary nodes is synchronized with that in the primary node, when a node fails, data is not lost.





        Figure 7-9. MongoDB primary/secondary cluster architecture

        The cluster ensures the set always contains exactly one primary node, even when the primary node fails. The secondary nodes maintain heartbeats with the primary node and with one another. When the primary stops communicating with the other members of the set, the secondary nodes elect one of the secondaries and make it the new primary. If the original primary becomes available again, one of the new primaries is demoted to become a secondary so that only one primary node remains.

        The primary node receives all write operations from the database clients so that it can maintain data consistency. By default, clients read from the primary, but clients can specify a read preference to send read operations to secondaries. However, because of asynchronous replication, reads from secondaries may return data that does not reflect the state of the data on the primary.

        Because all client write operations and most client read operations in a MongoDB database go through the primary node, it can become a throughput bottleneck and single point of failure (temporarily). A MongoDB database is more resilient than a database that runs in a single server but can be less resilient than other Replicated Databases.

        Redis Cluster

        A Redis cluster is a variation of a Redis database that runs in a

        cluster of multiple equivalent nodes, as shown in Figure 7-10. Each node can run on a different computer in the cloud, distributing the nodes to avoid a single point of failure and making the database run reliably on unreliable infrastructure.



        Figure 7-10. Redis grid cluster architecture



        A Redis database cluster is a mesh where every node is connected to every other node in the cluster via the cluster bus. Asynchronous replication propagates updates to replicas. While the nodes are equivalent, they can run in two different modes. A primary node can service read and write operations, whereas a secondary or replica node can only service read requests. Clients can connect to any node; the cluster routes write requests to primary nodes and read requests to any primary or replica node.

        A Redis cluster can remain operational when partitioned, such as when some of its nodes fail or the network fails. However, at most one partition remains operational. The operational partition must contain the majority of the primary nodes that are reachable and must also contain at least one reachable replica for every primary node that is no longer reachable. Any other partitioned nodes are unreachable. If the reachable nodes are insufficient, the entire cluster fails until it recovers.

        Apache CouchDB

        An Apache CouchDB database runs in a cluster of equivalent

        nodes, as shown in Figure 7-11. Each node can run on a different computer in the cloud, distributing the nodes to avoid a single point of failure and making the database run reliably on unreliable infrastructure.





        Figure 7-11. CouchDB peers cluster architecture

        Clients access the database through a load balancer that distributes requests across the nodes. Any node can perform both read and write operations.

        All of the nodes in the cluster synchronize via the network. When data is written to one node, the cluster propagates the update to the other nodes asynchronously.

        When the cluster becomes partitioned, each partition operates independently, serving the clients that can reach it. When partitioning is resolved and all of the nodes in the cluster are reachable, they all propagate their updates to resynchronize. When the resynchronization detects conflicts where the same document was updated differently in partitioned replicas, it logs the conflict for manual remediation.
        """,
    "Configuration Database":
        """
        Configuration Database

        (aka Distributed Coordination Service)

        You are implementing a cloud service – not a Cloud Application

        but a service that an application can use as a Backend Service . It will run distributed across multiple computers in the cloud.

        How can a cloud service store its service state such that all of the nodes in the service can share and access the state?

        A cloud service runs in multiple redundant nodes across

        multiple computers. Much like a Replicable Application , distribution across multiple nodes improves a cloud service’s resiliency, availability, scalability, and performance. Multiple nodes make a cloud service more resilient on unreliable cloud infrastructure: when one node fails or becomes inaccessible on the network, the cloud service is able to keep running properly on the remaining nodes.

        Replicating nodes is simpler for an application than for a cloud service because a cloud-native application is stateless, whereas

        most cloud services are stateful. An application with a Cloud-

        Native Architecture is not only a Replicable Application but is

        also a Stateless Application that stores its state externally. The state in a Stateless Application goes in the Backend Services, which therefore are stateful. For example, databases store data, secrets managers store credentials, monitoring services log events, and API gateways track requests. When a cloud service runs distributed across multiple nodes, it needs to share its state across those nodes.

        Most cloud services are also configurable. When an administrator changes the configuration in one node, the other nodes must also update with those configuration changes.

        The cloud service needs to store its state independently of any one node and continue to be able to share its state across the operational nodes. A cloud service needs data storage that does the following:

        Ensures that all of the nodes in the service can access and

        update the shared state at all times

        Ensures that the entire service and each of its operational

        nodes retain access to the shared state when nodes fail

        Ensures that each of the nodes in the entire service is notified

        when configuration data changes

        A cloud service could use raw storage, such as block or file

        storage, to store its state. But as Cloud Database explains, raw storage makes data difficult to replicate and to read as individual records.

        Data stored in multiple copies on multiple computers to survive

        when a node fails—that sounds like a job for a Replicated

        Database . However, most replicated databases employ eventual consistency, which can be a huge problem for the nodes in a cloud service. For the service to work correctly, all of its nodes need to work the same at all times, which means they all need to see the latest data at the same time and cannot wait for it to eventually show up.

        A cloud service needs to store its state in something that has all of the advantages of a replicated database but none of the disadvantages.

        Therefore,

        Store the session state for a cloud service in a Configuration Database, a Replicated Database that is reliably consistent and notifies all of the nodes whenever the data changes.

        A Configuration Database is a Replicated Database, so it consists of multiple nodes, each a server process coupled with its own storage. Unlike a Replicated Database, a Configuration Database is reliably consistent, providing all clients the same single

        version of the truth at all times. See Figure 7-12.





        Figure 7-12. Configuration Database

        A Configuration Database’s reliably consistent state means that once a record is updated in any node, all of the nodes have the update, so a read from any node always gets that latest data. Clients see the same data at the same time, and writes are immediately visible to all clients. A Configuration Database typically employs the leader-follower replication model, where a single leader node coordinates updates and maintains the latest set of data.

        A Configuration Database achieves reliably consistent data by doing what a Replicated Database normally avoids: it performs each update as a long-running distributed transaction. A write to the database is not complete until a majority of the nodes have recorded it. The Configuration Database still provides very good performance, handling thousands of reads and writes per second. It also enables clients to register for notification when the data changes, so a client using a record knows its data has changed.

        A Replicated Database that keeps its data reliably consistent sounds too good to be true, so of course there are limitations. To maintain reliable consistency and never return an incorrect result, it favors consistency over availability. When a Configuration Database becomes partitioned, the partitions become either read-only or unavailable. A Configuration Database is able to keep its data reliably consistent by restricting the format of the data and the amount of data it can manage. The database can scale across many nodes, but it is optimized for small amounts of data.

        To make its data easy to manage and quick to access, a

        configuration database typically is a Key-Value Store that stores its data as key-value pairs organized in a hierarchy. The database does not support querying other than lookup by key. Clients access and modify data using simple get and set operations that specify the key. The database does not try to parse the values, storing each one as a binary or character large object (BLOB or CLOB). Clients register for notification by specifying the keys of the records they depend on.



        A Configuration Database is reliably consistent with high throughput, but that works for only relatively small amounts of data, and it has to be formatted as key-value pairs. A configuration database is specialized to store the configuration for cloud services. Reusable services often have to deal with issues of availability, performance, and security stemming from multitenancy that most standard applications do not need to be concerned with. As such, they need lower-level access to how their topology is managed, controlled, and serviced than most applications do.

        There are some challenges with Configuration Databases. With very complex systems, it can be difficult to anticipate the impact of small configuration changes. For example, a change as small as an incorrect digit in a port number for a database connection could render an entire system inoperative. Therefore, you need to make sure that the data is up-to-date, accurate, and complete. If configuration changes affect multiple systems, it can be challenging to trace the full impact of the change across all the systems.

        Applications typically need a more general-purpose database—

        an Application Database , particularly one that favors Availability over consistency when partitioned and that supports storing large amounts of data in a variety of formats. Many Application Databases in turn use a Configuration Database as part of their implementation so that a database cluster can configure all of its replicated nodes consistently as they each persist large amounts of data.

        Each cloud service stores its own configuration data separately,

        making that data a Data Module .

        Different cloud services do not all have to store their configuration data in the same type of Configuration Database.

        Instead, cloud services can use Polyglot Persistence , where each cloud service can store its configuration data in a different type of Configuration Database.

        Like any cloud database, a Configuration Database can be

        hosted by a cloud platform as a Database-as-a-Service .

        Examples

        Three common Configuration Databases are etcd, ZooKeeper, and Consul. Many Application Databases incorporate these Configuration Databases into their own implementations.

        Etcd

        Etcd, Cloud Native Computing Foundation (a CNCF project), is a distributed, consistent Key-Value Database for shared configuration that keeps working through node failures and network partitioning. Etcd gained fame as the Configuration Database used to implement the Kubernetes container orchestrator, storing the desired state and current state for all of a Kubernetes cluster’s nodes and containers and enabling all of the nodes to maintain a consistent view of the state of the cluster at all times.

        Etcd employs the leader-follower replication model using the Raft consensus algorithm to distribute states across a cluster of computers. A client can connect to any etcd node to perform an update, but when the node is a follower, it forwards the update request to the leader, which logs the update and tells the followers to do so. When a quorum of the followers confirms the update, the leader confirms it to the client, and it becomes the new value for all nodes. When the leader becomes unavailable, the followers elect a follower and promote it to the leader.

        For more details about the Raft consensus algorithm, see the

        section “Database Topology and Database Selection”.

        Apache ZooKeeper

        Apache ZooKeeper enables highly reliable distributed coordination through a centralized repository of configuration

        information. ZooKeeper was created by Yahoo as part of

        Hadoop, who donated it to the Apache Software Foundation. It became famous when Netflix incorporated it into Netflix OSS,

        their Open Source Software foundation for Microservices .

        Like etcd, ZooKeeper employs the leader-follower replication model. Writes to a follower are forwarded to the leader, which acknowledges the write when the followers have updated.

        HashiCorp Consul

        Consul by HashiCorp has many features, including a distributed coordination service implemented as a distributed Key-Value Database for storing configuration data and other metadata. It also provides service mesh features like service discovery with health checks and encrypted communication between services.

        Like etcd and ZooKeeper, Consul employs the leader-follower replication model implemented using the Raft consensus algorithm.

        Distributed Databases

        Many database services use Configuration Databases to centrally store configuration information:

        Apache HBase

        Also part of Hadoop from Yahoo, is a distributed

        Columnar Database that is built on top of Apache Hadoop and uses ZooKeeper for distributed coordination

        Apache Cassandra

        Donated by Facebook, is a distributed NoSQL Columnar Database that uses a peer-to-peer architecture and ZooKeeper for distributed coordination

        CockroachDB

        A distributed SQL database (a Relational Database ) that uses a hybrid logical clock and vector clock algorithm based on Raft and etcd for distributed coordination and consensus

        On the other hand, many Cloud Databases do not incorporate etcd or ZooKeeper but instead implement their own

        synchronization mechanisms. These include Apache CouchDB

        and Redis Cluster .
        """,
    "Application Database":
        """
        Application Database

        You are writing a Cloud Application or Microservice structured

        with a Cloud-Native Architecture , so it is a Stateless Application . Yet a Stateless Application has state and needs to persist it.

        How should a Cloud-Native Application store the data it uses so that it can run as a Stateless Application?

        As Cloud Database explains, a Cloud Application should store its data not in raw storage but in a database. The question then is what capabilities a database should have to work well for Cloud Applications.

        Cloud Applications strive not merely for high availability but for continuous availability. Yet most applications are highly dependent on their database, so an application is only as available as its database. A cloud database needs to also be

        continuously available. A Replicated Database can have very high availability, but when the cluster becomes partitioned, consistency and availability become a trade-off.

        Cloud Applications strive for scalability, which means they not only need to serve more users but also need to store more data for those users. As more users perform more tasks, they use more data, so the applications need to access more data more quickly to serve all of those users. The easier it is for an application to access its data, the less code application developers have to write, and the application will get better performance accessing data.

        A Cloud Application needs a database that is highly available, even if that means its data becomes inconsistent temporarily. It needs to be able to scale in multiple respects: store large amounts of data, enable the application to access the data easily, and support large numbers of users concurrently accessing data.

        Therefore, Store the domain data for a Cloud-Native Application or a Microservice in an Application Database, one that like the application is highly available, can store large amounts of data, scales to support numerous concurrent users, and simplifies data access for the application.

        An application database tends to be a Replicated Database, although some types distribute across multiple nodes better than others. Some are reliably consistent, but the ones that distribute well tend to use eventual consistency. No one diagram can capture this range of capabilities, but the important feature to focus on is availability.

        As shown in Figure 7-13, as a Replicated Database, an Application Database runs across multiple nodes. When one of the database’s nodes becomes unavailable due to failure or network partitioning, the database uses the remaining functional nodes to keep working, keeping the database available so that the application maintains access to its data.





        Figure 7-13. Application Database

        When one node becomes unavailable, the data remains available in other nodes. A database typically replicates a minimum of three copies of each data record in three different nodes but may replicate many more copies to survive losing a large number of nodes. For ultimate availability, a database can not only run a large number of nodes but also replicate all of the data across all of the nodes, so then a single surviving node can still keep the database available.

        There are lots of ways to replicate across multiple nodes. For an

        exploration, see the section “Database Topology and Database

        Selection”.

        There are many types of cloud application databases, which fit into three broad categories:

        SQL databases

        These traditional Relational Databases employ relational algebra to organize data into tables, rows, and columns that clients can search and filter using structured query language (SQL). SQL databases are well-suited for applications that require complex queries, transactions, and referential integrity and are often used in enterprise environments.

        NoSQL databases

        These are non-Relational Databases that do not use SQL as their primary query language. They are designed to handle large amounts of unstructured and semistructured data, and are often used in environments where scalability and high availability are important. NoSQL databases are often used in web-scale applications, such as social networking sites, online retailers, and other applications that require fast read and write

        performance. NoSQL Distilled describes many different aspects of NoSQL databases.

        NewSQL databases

        These are a new generation of Relational Databases that are built to provide the scalability and high availability of NoSQL databases, while still maintaining the transactional consistency and SQL support of traditional SQL databases. They are often used in environments where both scalability and strong consistency are important, such as in financial and ecommerce applications. NoSQL databases are typically less efficient at SQL-like queries because of differences in approaches to query optimization. For an application that depends on SQL-centric complex query capability, a solution such as a NewSQL database or a distributed in-memory SQL database may be more efficient.

        All of these categories are Application Databases, but they differ in how they store data and make it accessible to applications, making some easier for some types of applications to use and others better suited for other uses. They optimize their querying and update capabilities for a particular mechanism of data storage and retrieval optimized for different application requirements:

        Some applications need a database to be highly optimized for

        efficient reads, while others need it to be equally efficient at

        reading and writing.

        Some applications need to simply store data as is and

        retrieve it in its original format, whereas others need the

        database to understand the data format to facilitate

        searching and navigating it.

        Some applications need a database to enforce data format,

        whereas others want a database that can handle variable

        formatting.

        No Application Database is a one-size-fits-all solution, so there are many different ones to choose from.



        Application Databases are databases, so they facilitate storing and managing large amounts of domain data and enabling applications to easily access and manipulate individual data records. A range of Application Databases differ in the trade-offs they make between consistency, availability, and scalability. And perhaps most importantly, they differ in the way they store and organize data and the types of data they are designed to handle.

        Because of the range of database categories, it is important to choose the right database structure and retrieval mechanism for the job the application needs to perform. Performance, scalability, and other application requirements will determine the particular type of database to choose. An application’s component design should be the driving factor in selecting a database, not the other way around. That is true in both the structure of the data the application is storing and in the way in which the application needs to query or search data.

        Compared to an Application Database, a Configuration Database is much more specialized. It manages a much smaller amount of data and only supports looking up data record by their keys with no querying. It scales across numerous nodes while keeping its data reliably consistent, but it does so by favoring consistency over availability, whereas applications strive for availability.

        There are several types of Application Databases. Each type works best for certain requirements:

        Relational Database

        Works well for relational data, an acknowledgment to the fact that relational representations are still sometimes the right way to store and manage certain types of application data. SQL and NewSQL databases are optimized for scalability and free-form querying.

        Document Database

        Works most like a relational table row that the database can easily replicate across multiple nodes. The records are schemaless JSON data, much like the parameters in web services. The documents can be searched but not easily reformatted to entirely new configurations as in the Relational Database approach.

        Key-Value Database

        Works like a hash map, enabling an application to access unstructured data directly with O(1) performance for many use cases.

        Graph Database

        Excels at storing entity-relationship-attribute (ERA) data structured as entities with relationships and attributes, and at easily traversing those relationships from one entity to another. This works well for the data in social media networks, travel networks (highways or flights), and the mathematical operations for constructing and formatting large-scale neural networks.

        Columnar Database

        Works well for data analytics, storing well-structured data and enabling rapid access to all records with a specified value.

        A single large application may make use of multiple Data

        Modules that are independent of one another. Different modules may require support for different data types and

        access styles, so Polyglot Persistence enables an application to store each module in a different type of database. Each database should ideally be hosted by the cloud platform as a

        Database-as-a-Service .

        Examples

        The IT industry offers many different database products and open source projects that are suitable for applications to use to store their domain data. Examples of each Application Database category include the following:

        SQL databases

        SQL Relational Databases include Oracle database, IBM

        Db2, Microsoft SQL Server , PostgreSQL, and MySQL. Public cloud platforms host SQL database services based on those products.

        NoSQL databases

        Examples of NoSQL databases include MongoDB, Apache

        CouchDB, Redis, and Memcached. Cloud services include

        ones that host those products as well as IBM Cloudant,

        Google Cloud Datastore, and Amazon DynamoDB.

        NewSQL databases

        NewSQL databases include CockroachDB, MariaDB Xpand

        (originally known as Clustrix), and SingleStore (originally known as MemSQL). Public cloud NewSQL databases

        include Google Cloud Spanner and Amazon Aurora.

        As shown earlier, major public cloud platforms host many of these types of databases as services and host their own cloud-only databases as well.
        """,
    "Relational Database":
        """
        Relational Database

        You are writing a Cloud Application or Microservice structured

        with a Cloud-Native Architecture and are selecting an

        Application Database for your application to use to persist its domain data.

        How can an application store well-structured data that it needs to query dynamically?

        Cloud vendors often support newer databases generally categorized as NoSQL databases. Developers often assume that a cloud database is always a NoSQL database, but not all applications and not all data lend themselves well to NoSQL databases.

        Most existing data in an enterprise’s traditional IT systems is typically stored in tables in a relational database management system (RDBMS). When the data is already structured to be stored in well-defined tables, converting it to a NoSQL format often provides little benefit.

        An enterprise’s existing traditional IT applications are typically written to use an RDBMS. The applications expect to have data that are well-structured records, or access those records by performing CRUD operations (create, read, update, and delete), to update those records using ACID (atomic, consistent, isolated, and durable) transactions, to query the records using SQL (structured query language), and to take advantage of database views to structure the same data as different record formats for different uses. As long as the application works well as is, a NoSQL database provides little advantage and in fact will require significant modifications to keep the application working.

        Even when developing new Cloud Applications that need to store new data in a cloud database, a NoSQL database may not be the best choice. An application’s data may naturally be well-structured, such as the records gathered from users filling in forms. The application’s domain logic may do little more than CRUD and query the data. An application like this needs a database that is optimized for performing these functions on well-structured data, which is probably not a NoSQL database.

        If a new or existing application would work well on traditional IT using an RDBMS, a NoSQL database in the cloud will actually make it work worse.

        An advantage of many NoSQL databases on the cloud is that they provide better availability than a traditional IT RDBMS does. Many NoSQL databases run distributed across multiple nodes so that if one node fails, the others keep the data available. Ideally, applications should get the availability of data stored in a NoSQL database without having to convert RDBMS data to NoSQL.

        Therefore, Store well-structured data that applications will query frequently in a Relational Database—hosted in the cloud.

        A Relational Database is an Application Database that stores its data formatted as a schema of tables, rows, and columns. It enables an application to search its data using SQL queries and can use database views to present the same data in different formats. A Relational Database implements ACID transactions, so it favors consistency over availability. Yet a Relational Database can run in multiple active processes to maximize availability and scalability, making at least some of its data

        available at any given time. As shown in Figure 7-14, a Relational Database stores each table row once, a single consistent source of truth for that row’s data.

        A Relational Database is usually a Replicated Database , but some Relational Databases replicate better than others. Older SQL databases run active-standby, with a single active node that stores all of the data and handles all client requests, and a standby node that stores a copy of the data. Newer SQL databases run in multiple active nodes.

        The trick for a Relational Database running in multiple active nodes is to implement ACID transactions that preserve the data’s consistency and referential integrity. The database achieves this by storing each table row in only one node and storing related table rows in the same node. One copy of each table row acts as a single source of truth for the record, and storing related table rows in the same node enables the node to maintain referential integrity within the data. Storing a table row in a single node makes the node a single point of failure for all of its table rows. The database can compensate for this shortcoming by maintaining a standby copy of each active node.

        A Relational Database server can host multiple schemas (i.e., a set of tables) in the same node but can also host each database in a different node.





        Figure 7-14. Relational Database

        Some Relational Database servers not only distribute different databases to different nodes but also distribute a schema’s tables across nodes, and can even split a single table and distribute it across nodes (this is called partitioning and is

        described in detail in the section “Database Topology and

        Database Selection”). Figure 7-14 shows a single table, Table 1, split across two nodes, Database Node A and Database Node B. It stores each of the table’s rows in a single node, but some of the rows are stored in one node, while other rows in the same table are stored in another node. The database uses distributed queries to search a table split across nodes, running the query in both nodes and merging the results. The diagram also shows a set of records normalized across two tables, with the rows in Table 3 referring to rows in Table 4. Because of this relationship, the database stores both tables in the same node, Database Node C, and that node is responsible for maintaining the referential integrity within the data.

        Using these techniques, a Relational Database can achieve massive scalability and wide distribution while preserving ACID transactions and efficient querying.



        A Relational Database can be a good choice for a cloud-native application or Microservice that needs access to existing relational data or has well-structured data it needs to be able to query easily. The Relational Database enables moving existing relational data to the cloud without needing to significantly alter the data or the applications that use it. It also offers great flexibility for searching the data and presenting different views of the same data for different uses. Many Relational Databases are more highly available and scalable than their traditional IT counterparts while still preserving ACID transactions.

        While a Relational Database can be highly available as a whole, the availability of any one record can be more limited. Each record is stored in a single node, so when that node becomes unavailable, that record becomes unavailable unless and until the database replaces it with a standby node.

        A cloud-native application or Microservice is often implemented with an object-oriented language such as Java, especially code developed using techniques like domain-driven design. Storing data in a Relational Database necessitates object-relational mapping (ORM), which can be difficult to develop and maintain and can perform poorly at runtime.

        Many cloud-native applications and Microservices work better

        with a Document Database in which semi-structured data is stored the way the application represents it. While Document Databases are often highly scalable and available, the data can become inconsistent temporarily and inefficient to query, shortcomings a Relational Database does not share.

        Sometimes the data in a Relational Database is just binary or

        character large objects (BLOBs or CLOBs). A Key-Value Database can store unstructured data more efficiently and optimize access.

        Relational Databases are terribly inefficient at following relationships between data because doing so requires

        performing querying and joins across tables. A Graph Database maintains referential integrity between entities and simplifies navigating relationships efficiently.

        A Relational Database is for storing and accessing rows of data. When an analytics program is interested in all of the unique values in a column and not in the rest of the data in the row,

        use a Columnar Database .

        An application using a Relational Database should use it to store

        a single Data Module and use Polyglot Persistence to store modules of table data in Relational Databases and modules of other data formats in other types of databases.

        A Relational Database should be hosted by the cloud platform as

        a Database-as-a-Service . Most public cloud platforms host multiple table DBaaSs.

        Examples

        There are literally dozens of examples of Relational Databases. The oldest and most familiar ones are enterprise SQL databases. An application does not require a traditional enterprise database to use SQL. At least two other types of databases also implement SQL: Small SQL and NewSQL.

        Enterprise SQL

        Databases for hosting an enterprise database of record include

        Oracle database, IBM Db2, and Microsoft SQL Server . These have usually been hosted on traditional IT, and many public cloud platforms host at least some of these databases as a

        service (Database-as-a-Service or DBaaS).

        Small SQL

        Small SQL databases such as MySQL and PostgreSQL have these advantages:

        These databases are very well supported, both by the open

        source community and by many vendors. It is relatively easy

        to find documentation and tutorials for them and to find

        developers skilled in them.

        These databases are small and lightweight enough to

        containerize easily and deploy and update through the same

        GitOps mechanisms used to deploy application code.

        These databases are supported in DBaaS services on the

        public cloud platforms.

        A major shortcoming of Small SQL databases is that, as the name implies, they often do not support the same level of scale (particularly with regard to sharding) that enterprise databases can provide.

        NewSQL

        Scalability is where NewSQL databases shine. They combine the best attributes of Small SQL databases and the scalability of

        NoSQL databases. These include CockroachDB, Apache

        Trafodion,, MariaDB Xpand (originally known as Clustrix), and

        SingleStore (originally known as MemSQL). Public cloud

        NewSQL databases include Google Cloud Spanner and Amazon

        Aurora.

        NewSQL databases can be a good choice for any application that needs ACID transactions, an SQL engine that fully supports the relational model, and extensive scaling and sharding capabilities. Yet that choice comes at a cost—these databases are often more complex to set up and manage than the older Small SQL solutions. It is also harder to find people with skills in these databases. Regardless, when selecting a Relational Database, these should be considered as options. 
        """,
    "Document Database":
        """
        You are writing a Cloud Application or Microservice structured

        with a Cloud-Native Architecture and are selecting an

        Application Database for your application to use to persist its domain data.

        How can an application most efficiently store and retrieve data when the future structure of the data is not well known?

        When developing a new application, often the requirements for the domain data it will need to persist are rather unknown. As the application evolves, the data format can change. The

        application could start out using a Relational Database with a schema for well-structured data. By the time the data requirements are well understood and the data format can be designed accordingly, it may be too late and the application is locked into the existing schema.

        One of the advantages of cloud is that it supports agile development. An application can start as a minimum viable product (MVP) and then incrementally improve as new features are discovered. For an application to evolve easily, its database must be able to evolve easily as well. A Relational Database with a strict schema is difficult to evolve. If early deployments of the application have created data, migrating the data to new versions of the schema becomes cumbersome.

        Another aspect of agile development is that an application must be able to access data easily. Relational Databases require applications to implement object-relational mapping (ORM) code to transform the relational data into the application’s domain object model and back again. When developers spend time writing code to make the application work with the database, they aren’t developing user functionality. The application needs a database that works the way the application does, storing data in the same format the data uses with minimal mapping. The database should make it easy for an application to access a set of data that it needs as a single record that can easily be read or written as a single task.

        While a Relational Database is designed to store well-structured data, much of the world’s data is not well-structured data. Real-world data tends to be semi-structured, with enough structure to figure out what its fields are but with variability in the structure from one record to the next. Even storing something as common as a customer’s mailing address or phone number becomes complicated for an enterprise with an international customer base. Trying to store data with such variable formatting in a fixed schema is difficult.

        A Cloud Application needs to scale the way the cloud does, and

        so does its database. A Cloud Application needs a Replicated

        Database with the same availability, scalability, and performance that the application has. A Replicated Database runs in multiple nodes that can be distributed across multiple computers and make use of multiple sets of storage, enabling the database to grow and run reliably even on unreliable cloud infrastructure.

        Therefore,

        Store the application data in a Document Database, a database that structures its data the way the application does.

        A Document Database is a kind of NoSQL database and is schemaless, so it can store data without a predefined schema, simply by storing data the way the application delivers it. A Relational Database and a Document Database both store domain entities, but rather than storing each entity as a table row normalized across several tables scattered across the disk drive, it stores each entity a single document that it can access in one easy step from one area of the disk drive without joins. A Document Database typically represents its data externally as JSON data. It is typically a Replicated Database that runs in multiple nodes and replicates each document across those nodes.

        Figure 7-15 shows a Document Database running in three database nodes that stores two documents and has replicated both of them to all of its nodes. The database can route each client request to any of its nodes. Since every node stores a replica of all of the data, any node that receives the client request can serve its data. If each node replicates only some of the data and a client requests data in another node, the node that receives the request can redirect it to a node that stores a replica of the data.

        A Document Database enables the data to evolve as the application evolves, facilitating agile development. A Document Database does not have a fixed schema for its data. Most Document Databases represent their data externally as JSON data, which doesn’t mean that’s how the database stores it necessarily but explains how the database’s client APIs format data to be read and written. JSON records are nested with individual key-value fields at each level, so the database understands the structure of the data. Yet JSON can structure any data this way, and then so too can a Document Database. By simply persisting the JSON data as is, the database doesn’t require any prior knowledge of the data’s structure and doesn’t force the data to fit into any predefined structure.





        Figure 7-15. Document Database Many Cloud Applications and web applications already structure data as JSON, so doing it for the database is natural and no extra effort. Even if your application is not written in JavaScript and thus already uses JSON, there are available libraries to serialize and deserialize JSON into object structures in Python, Java, Golang, and most other languages. A JSON-structured Document Database makes it easy to store the data the way the application is already using it and to read the data back in that format, which makes the database easy for the application to use and makes tasks efficient because so little data transformation is needed. No ORM is needed since the database and the application use the same structure to store the data. Because the database understands the structure of the documents, it can facilitate more efficient querying by indexing the shared attributes across many different item types.

        A Document Database makes persisting data much easier so that developers can focus their efforts on implementing user requirements. Document Databases model their data the same way their applications do and do not normalize their data beyond the normalization that the application does as part of modeling the domain. When the application has data about a customer, product, or account and persists it to the database, the database stores all of that data as a single record—a document. The database can easily replicate that document to other nodes as an atomic unit. Every document has a unique ID and a revision ID, making it easy for the database to keep track of replicas in different nodes, as well as determine which replica has the latest revision and which ones need to be synchronized. Two-way replication—where some changes occur in one node and some in another and need to be synchronized in both directions—is relatively easy to perform. Meanwhile, the application has complete flexibility to normalize the data the way the domain does naturally. If multiple members of a household share the same house, the application can store that house once and share it among records for multiple residents. This same structure is persisted in the database and can be navigated by the same relationships.

        A Document Database also has shortcomings. Because a Document Database offers so much flexibility in how it stores data, the database has little ability to enforce data consistency or referential integrity, pushing those responsibilities back into the application. Very large documents can limit performance, compelling the application to decompose (i.e., normalize) a large document into smaller ones that it can query and access individually.

        A Document Database works the way a Cloud Application does, storing semi-structured data in the same format the application uses, storing each data entity as a document, and enabling individual documents to vary in format. A Document Database makes agile development easier because it requires limited code in the application for persistence and can evolve with the application. As Replicated Databases, Document Databases can be highly replicated for maximum availability on unreliable infrastructure.

        Document Databases make data easy to store and retrieve but do not enforce data consistency or referential integrity. Querying the data may not perform well.

        For well-structured data, consider a Relational Database for a database that enforces data consistency, maintains referential integrity, and optimizes query performance.

        For unstructured data that cannot be queried, consider a Key-

        Value Database for a database that provides direct access to binary or character large object (BLOB or CLOB) entities via keys.

        For data where the applications navigate the relationship between the entities more than they use the data in the entities,

        consider a Graph Database , which manages each entity like a document but is optimized for lookup via references.

        An application using a Document Database should use it to store

        a single Data Module and use Polyglot Persistence to store modules of document data in document databases and modules of other data formats in other types of databases.

        A Document Database should be hosted by the cloud platform as

        a Database-as-a-Service . Most public cloud platforms host multiple document DBaaSs.

        Examples

        Document Databases are NoSQL databases, but not all NoSQL databases are Document Databases. (Others are Key-Value Databases or Graph Databases.) There are a number of common Document Database products and public cloud platform services. A common example of an application using a Document Database is an ecommerce application storing a catalog of products.

        Document database products and projects

        These products and open source projects implement Document Database:

        MongoDB

        A very commonly used Document Database that is distinguished by its flexible schemas, powerful built-in query capability, and scalability and availability

        Apache CouchDB

        Incorporates synchronization techniques from Lotus Notes that features built-in conflict resolution and supports incremental replication

        Couchbase

        A document-oriented database that emerged from the team that built Memcached

        Many cloud platforms also host these databases as DBaaS services.

        Cloud platform document databases

        These cloud platform services provide a Document Database (as a DBaaS):

        IBM Cloudant

        Built on Apache CouchDB

        Amazon DynamoDB

        Supports the document model in addition to the key-value model

        Amazon DocumentDB

        Compatible with MongoDB

        Azure Cosmos DB

        Can be used as a Document Database or a Relational Database

        Google Cloud Firestore

        A document-oriented database that supports the Google Firebase application development platform

        In most cases, the particular product you choose matters less than how well suited your particular usecase is for a Document Database.

        Document Database ecommerce example

        When making a decision as to which NoSQL database to choose for any particular Microservice, perhaps the default, first type to consider should be a Document Database. As stated earlier, Document Databases have the flexibility to represent anything that can be serialized as a JSON document—which includes most object structures in most languages. Thus, for simple object structures where the individual objects are going to be searched by any one of several fields of the objects, it’s a good solution to start with.

        An example of this that we have seen in the ecommerce field is

        a product catalog. In the online ordering example for Bounded

        Contexts , we discussed how most users will begin their interaction with the catalog by performing a search. However, we left the details of that search to be defined later!

        Searching a product catalog can be a difficult process, because representing a product can be complex. Different types of products have different attributes, so there is no single product type with a fixed schema. It is difficult to model products in a Relational Database because different types with different attributes need different schemas, such as different database tables. The data for all of the products in each table has to fit that schema, even if some products are missing some attributes or have extras. Then all of the different tables need to be searched differently.

        A Document Database can keep all products in a single group, where the data for each product lists whatever attributes it needs. Products can be searched by any attributes that seem relevant, enabling customizable searching. If a product doesn’t have a particular attribute that’s part of the search, the search can assume a default value or ignore that product as not a match. If all products had the same attributes, a Relational Database might be the best solution. But when they do not, a Document Database may well be a better solution.

        Let’s consider a couple of simple examples of different product types. The first is something simple, like laundry detergent. The product description, size of the container, and manufacturer are most of what someone might search. That’s a simple product representation. However, searching for soft goods like clothing involves several different aspects that weren’t part of the laundry detergent example—gender, sizes or measurements, colors, and materials all would be added to the fields already described for simple products. You may want to display many more pictures of a piece of clothing than you would for a container of laundry detergent as well.

        At one online merchant we worked with, the most complex search of all was for car tires. Specifying a tire involves not only complex sizing and description codes but also lots of additional attributes about the tire itself—for instance, the weather it’s for and the details of the warranty on the tires. Complicating this was the fact that very often people would search not by any attribute of the tire but by the vehicle models that the tire is designed to fit!

        All of these add up to different object representations, perhaps even an inheritance hierarchy rooted at simple catalog items, and then with subclasses or other separate representations for specialized types like clothing or car tires. Any or all of these attributes will need to be searched, and what’s more, as the catalog expands and new items are added to the products the vendor carries, they want to want to be able to do that quickly, without having to change any of the existing catalog contents. This is why a Document Database is perfect for this particular problem. You may not only have different representations of the different products but also build and optimize (index) different searches for all these different cases and add to it on the fly.
        """,
    "Key-Value Database":
        """
        Key-Value Database

        You are writing a Cloud Application or Microservice structured

        with a Cloud-Native Architecture , and are selecting an

        Application Database for your application to use to persist its domain data.

        How can an application most efficiently store and retrieve independent data entities that are always looked up by the same key?

        Sometimes an application wants to store an isolated data record using a unique ID that the application can use later to retrieve the record as is. The application doesn’t need to query the database to look for the record; the unique ID specifies the exact record the application needs.

        This scenario is common for session management and for caching data. A session stores data for a web application on the server to track the history and context of the web user. A database cache stores data retrieved from a database so that the application can avoid repeatedly retrieving the data from the database.

        When an application stores and retrieves data by specifying a unique ID, a database can easily index those data records. The database uses the unique ID as a key and stores the record indexed by that key. The next time the application specifies the same unique ID, the database uses that as a key to retrieve the record. The database can store the record as an atomic value and doesn’t need to understand the content or structure of the value it is storing. As far as the database is concerned, the record’s data type might as well be a binary or character large object (BLOB or CLOB).

        Other databases like Relational Databases and Document

        Databases add a lot of overhead that isn’t needed in this scenario. The records in those databases don’t necessarily have unique IDs, or those UIDs aren’t necessarily apparent to the application. The application expects to search for multiple records matching its criteria and does not assume the match will always be exactly one record. The database understands the structure of each record and the fields it contains, storing the field values separately and indexing certain ones to enable applications to query for those values. The database also understands the relationships between separate records, managing them as a collection and enabling an application to retrieve multiple related records more easily. This overhead is helpful for applications that use the data more generally but isn’t needed when the application knows the exact ID of the record it needs.

        Applications need a more efficient, specialized database without this general-purpose overhead.

        Therefore, When an application always performs lookup on the same key, store its data in a Key-Value Database optimized to work like a hash map.

        A Key-Value Database is a kind of NoSQL database and is schemaless, so it can store data without a predefined schema, simply by storing data the way the application delivers it. Key-Value Databases are often the most scalable type of database with the best performance. A key-value database is optimized to store unrelated, unstructured data records indexed by their unique IDs. It uses each record’s UID as a key and stores its

        unstructured data as a value. It is typically a Replicated

        Database that runs in multiple nodes, storing its data in one or more partitions (i.e., tables) that it replicates across multiple nodes.

        Figure 7-16 shows a Key-Value Database running in three database nodes that stores records in three partitions with two replicas of each partition. The database can route each client request to any of its nodes. If a node receives a request for a partition it does not store, it reroutes the request to another node that does store the partition.



        Figure 7-16. Key-Value Database A Key-Value Database works like a hash map in a programming language like Java. A hash map rapidly calculates the hash of the data in a key and uses that hash as an index into an array structure. The hash map uses the hash index to insert a value directly into the array and to directly access the value in the array to read it back out. A key-value database replicates that approach as a database that can store billions of individual

        values over multiple servers. Figure 7-17 shows the basic idea.





        Figure 7-17. Key-Value concept

        This simplicity is extremely useful for situations like the caching scenario described earlier, and Key-Value Databases are designed to take advantage of this simplicity. For simple key lookup operations, most Key-Value Databases offer O(1) performance. This is even true when the data is stored across multiple nodes in a cluster because it is easy to partition key-value data and prepend the partition ID to the key, forming a

        compound key, as is shown in Figure 7-18.





        Figure 7-18. Compound Key-Value

        The basic API for a Key-Value Database is very simple. The API is fundamentally two operations: get(key) and set(key, value) . Each key’s value is a primitive, such as a string (i.e., character array) or integer. For the SET operation, the database stores each value exactly as is. For the GET operation, the database returns the value as is, deferring to the application to interpret the value’s format. When setting a value with a key that is already in the database, the SET operation doesn’t update an existing record; it replaces any existing record.

        Many Key-Value Database implementations store each value as more of a document that has structure. The Key-Value Database may support value types such as string and binary, which are just CLOB and BLOB; other primitive types such as number, Boolean, and null; collection types like list, set, and map; and JSON, which is a string or CLOB that the database parses as a document. Databases that recognize these value types typically enable them to be indexed and enable applications to query on the values, which gives the database some Document Database functionality.



        Key-Value Databases excel at looking up data records by their keys. They are schemaless and handle unstructured data, storing it as is and returning it as is. This simple approach means they are usually the most scalable and best-performing type of database.

        Most Key-Value Databases make querying by value either impossible or quite slow. Every value within a partition needs a unique key; if two values in the same partition inadvertently use the same key, the last one replaces the one that was already in the database.

        If an application caches data using a Document Database , the performance may be significantly worse than it would be with a Key-Value Database. That is because Document Databases optimize for more complex cases such as searching by the contents of the documents stored.

        Sometimes an application stores its data in a Relational

        Database when it should instead use a Key-Value Database. For example, a Java enterprise application may persist its domain objects in a Relational Database, presumably storing the objects as relational data. Surprisingly, the persistence code in many of these applications serializes the objects and stores the data as BLOBs. This occurs as the result of a team throwing up their hands at the complexity of trying to map their domain objects into relational tables and columns. BLOBs in a Relational Database have many disadvantages: the database cannot query the data because it has no columns, and the database manages such huge blocks of data inefficiently. Worse, if improvements to the code change the object’s structure, the existing data may no longer be readable because the persistence code cannot deserialize it. This is a scenario where a Key-Value Database would work much better.

        There are multiple types of databases—the trick is to use the best tool for the job. A Key-Value Database is not always the best option. Rather than serializing Java objects, the persistence code may be able to use a database more efficiently by serializing the objects as JSON data rather than binary data and storing the JSON documents in a document database. When an application wants to search for data, a Key-Value Database is typically suboptimal if not useless, so the application should store its data in a Relational Database or Document Database.

        An application using a Key-Value Database should use it to store

        a single Data Module and use Polyglot Persistence to store modules of key-value data in Key-Value Databases and modules of other data formats in other types of databases.

        A Key-Value Database should be hosted by the cloud platform as

        a Database-as-a-Service . Most public cloud platforms host multiple key-value DBaaSs.

        Examples

        Here are some common Key-Value Database products and public cloud platform services, as well as a domain-specific example for caching session data.

        Key-Value Database products, projects, and services

        These products and open source projects implement Key-Value Databases:

        Memcached

        A free, open source, in-memory Key-Value Database that is specifically targeted at caching. It is very performant and

        is often used for storing session state and web page caches.

        Redis

        A source-available, in-memory Key-Value Database but one that is more generally usable for a variety of use cases. It has a more extensive API than the simple get-and-put semantics of Memcached, which makes it more useful as a general-purpose NoSQL database. As a result, it has become one of the most commonly used NoSQL databases.

        Valkey is a fully open source fork of Redis that was started in 2024 when the Redis license changed from open source.

        Riak KV

        A Key-Value Database built on a general-purpose, open source distributed systems framework, Riak Core. Riak is a formerly commercial product that went entirely open source in 2017. Other extensions of the Riak Core include Riak CS (Cloud Storage) and Riak TS (Time Series), demonstrating that it is possible to build multiple types of application databases on the same underlying distributed systems model.

        Ehcache

        An open source Java distributed cache project that is based on Key-Value Database functionality.

        These cloud platform services provide Key-Value Databases (DBaaSs):

        Amazon DynamoDB

        Supports both the key-value model and the document model

        Google Cloud Bigtable

        A Key-Value Database that is also a wide-column database

        (i.e., a Columnar Database ), meaning that it supports very wide tables with tens of thousands of columns

        Azure Cosmos DB

        Provides Key-Value Database functionality.

        While all Key-Value Database products function in the same way, they are optimized for different usecases. So you need to carefully consider your usecase when selecting a product. Session Data and Key-Value Databases

        As briefly described, a simple example of the use of Key-Value Databases that is very common is managing HTTP session data. We will use Java as an example; however, most web

        frameworks in other languages operate similarly. Jakarta

        Enterprise Edition defines the HttpSession object as part of its

        servlet framework for building Web Form Applications .

        This interface serves as a key-value lookup mechanism for managing the user’s state data (which can be literally anything but often represents selections the user has made on previous pages in a navigation). There are two approaches for storing HttpSession objects: in the JVMs and in a database.

        The default implementation of most application servers stores the HttpSession objects in an in-memory cache inside each web container’s JVM. Each user is identified by a unique value, the

        JSESSIONID , that is encoded either directly in the URL of the

        request or (more commonly) in a cookie that is stored on the user’s browser. In this cache, the key is the JSESSIONID , and the value is the user’s session data.

        This solution, while very simple, has a lot of downsides. The first is that if the JVM crashes, all of the customer records stored in that in-memory cache are lost. The second is that a complex routing solution (i.e., sticky sessions) is needed to ensure that user requests are always routed to the JVM that holds the entries for that particular user. This solution must be implemented in front of the JVMs being used as application servers, often in a frontend proxy like NGINX. All of this adds up to complexity that developers do not want.

        That is why many teams have turned to using Key-Value Databases like Redis or Memcached to instead store HttpSession data. The match between session data and a key-value store is so straightforward that it’s hard to imagine teams choosing nearly any other solution once they begin using them together. One common combination for users of the Tomcat server is to

        use Redis along with the open source Redisson library for using

        Redis as the backing store for HttpSessions. Likewise, Spring

        Boot users will use Spring Session to connect to Redis as a

        backing store. Commercial application servers like IBM’s

        WebSphere Liberty support the same type of functionality as well.
        """,
    "Graph Database":
        """
        Graph Database

        You are writing a Cloud Application or Microservice structured

        with a Cloud-Native Architecture and are selecting an

        Application Database for your application to use to persist its domain data.

        How can an application most efficiently store and retrieve interrelated data entities by navigating their relationships?

        When we think of the structure of data, there are some obvious ways of representing data that seem “natural.” Perhaps the most straightforward is with key-value data, where an application performs a lookup on a single field value to find another field value, or in document data, where an application stores data that reflects the way that people still tend to think in terms of separate pieces of paper, such as forms.

        But there’s a more challenging complex data type that we have to think about—and that is the data model, consisting not only of a simple data structure, like the attributes for a person, but also the very complex ways in which that person relates to other people and other entities like employers, property, and community organizations. A single person can belong to multiple different types of relationships:

        A Person relates to the other Persons in their family and

        has relationships with those family members.

        A Person relates to the people they work with and may

        have friendships and relationships outside of a company

        hierarchy—in other words, all of an employee’s friends and

        coworkers may not report to the same boss.

        A Person has friends that they may know through multiple

        different venues, such as social clubs, their neighborhood,

        school, etc.

        What this amounts to is that while it may be possible to represent a Person as a simple data structure, mapping out their social networks gets complicated. The data model starts adding more and more attributes to try to represent all of the relationships to other people. The problem is that all of these relationships are similar in some ways but different in others. A cousin can also be a friend, or a coworker could be someone you went to school with. Managing when a Person is removed from one subnetwork or added to another becomes complex. What is needed is a simple way to represent these different networks such that an application can easily navigate a particular network when it is focused on one particular type of relationship but that easily enables it to also explore how these relationships intersect.

        Therefore,

        Model and navigate relationships among entities with a Graph Database, which represents relationships as a mathematical graph with nodes (entities) and edges (relationships between nodes).

        A Graph Database is a kind of NoSQL database and is schemaless, so it can store data without a predefined schema, simply by storing data the way the application delivers it. Graph Databases excel at modeling domain entities connected to one another by numerous relationships. This capability simplifies implementing application functionality to determine the other entities that one entity is related to and then follow the relationships of interest to explore those related entities. Each

        entity is like a document in a Document Database , often represented externally as a JSON document, but a Graph Database gives much better support for modeling the entities’ relationships and navigating to other entities via their relationships. A Graph Database makes navigation much more

        efficient than querying. It is typically a Replicated Database that runs in multiple nodes and replicates each entity across multiple nodes.

        Figure 7-19 shows a Graph Database running in three database nodes that store six different entities—three people, two books, and a paper—and the relationships between the entities. What this doesn’t show is that the database typically replicates each entity and distributes the replicas across its nodes. The database can route each client request to any of its nodes. If a node receives a request for an entity it does not store, it reroutes the request to another node that does store the entity.

        Graph data fits the structure of an entity-relationship-attribute (ERA) model. An entity is an object in a domain. Its attributes are properties about the entity, similar to the columns in a table or the fields in a document. Its relationships point to other relevant entities.

        A Graph Database solves several types of problems more easily than comparable database types. For example, consider if an application needs to do any of the following:

        Navigate deep hierarchies

        An application may have the functionality to look for relationships in a very large family tree. For example, the

        University of Oxford has assembled the largest ever

        human family tree, one that contains 27 million individuals, both living and dead, in order to perform

        genetic research. Navigating this structure to track small genetic changes across tens of thousands of individuals spanning dozens of generations requires search optimizations that are simply not feasible in other database types like Document or Key-Value Databases.

        Find hidden connections between distant items

        This is where Graph Databases become helpful for optimization problems. For example, a transport network might have a bottleneck like a train derailment due to a washed-out bridge. To find another way around, a graph of data may show that two distant cities are connected directly through a different type of transport link (like a ship route) that ordinarily may not be an option, but may end up saving time in this situation. A similar example is graph theory’s traveling salesman problem (TSP), which searches for the shortest overall route through several geographically disbursed points.

        Investigate interrelationships between items

        This is the largest set of potential cases where Graph Databases shine. For example, navigating the complex web of websites a person visits is absolutely critical to making recommendations from retail websites based on shared interests, common attributes, and similarities.

        Graph Databases make these types of problems easier, simpler, and faster to solve.





        Figure 7-19. Graph Database

        While Graph Databases do have advantages, they also have somewhat significant drawbacks. The first is difficulty finding developers with the skills to use these databases. Graph

        Databases are not as widely used as Relational Databases , or

        even Document Databases or Key-Value Databases , so developers have less experience using them. What’s more, there is not a single dominant Graph Database, nor is there a commercial product or an open source project. That means that the user community of each database product is somewhat small and may make it difficult to find skills or obtain answers when problems occur.

        Another issue with Graph Databases is that there is not yet an accepted standard for graph queries such as SQL for Relational Databases. As a result, several query languages are available. For example, both Neptune and Cosmos support both Gremlin and SPARQL, while Neo4J supports the Cypher query language. This lack of standardization for the client API creates challenges when moving applications from one database to another, as well as for developers learning to write code that uses Graph Databases.

        There are also issues with the nature of graph data, which impact Graph Databases managing that data. For example, bulk updates are generally complex in a Graph Database, since each entity must be updated separately, and updating an entity also involves updating all the relationships to that entity. So, for example, if a company was splitting up, to split a company directory built in a graph database, the process would have to address each employee individually and re-create the new relationships separately. That can be slow and computationally expensive.



        Graph Databases naturally store data consisting of interrelated entities and simplify an application’s ability to navigate those relationships.

        However, Graph Database products are not widely used, so finding experienced developers is difficult. The querying API is not standardized, leading to vendor lock-in for applications using a particular database. Also, graph data is complex. Graph databases help handle the complexity, but management can still be difficult.

        There are multiple types of databases; the trick is to use the best tool for the job. A Graph Database is not always the best option. Entity data with few relationships can probably be managed

        more easily in a Relational Database or Document Database , especially for applications to search the data. If the entities are

        unrelated, they can be stored in a Key-Value Database .

        An application using a Graph Database should use it to store a

        single Data Module and use Polyglot Persistence to store modules of graph data in Graph Databases and modules of other data formats in other types of databases.

        A Graph Database should be hosted by the cloud platform as a

        Database-as-a-Service . Some public cloud platforms host graph DBaaSs.

        Examples

        Here are some common Graph Database products and public cloud platform services, as well as a domain-specific example implementing a recommendation engine.

        Graph Database projects, products, and services

        There are several Graph Databases in common use on the cloud:

        JanusGraph

        A Linux Foundation project, this is a scalable graph database optimized for storing and querying graphs.

        Neo4j Graph Database

        A scalable, open source graph database that is available as the Neo4j Aura cloud service.

        Apache TinkerPop

        A framework for graph databases that incorporates the Gremlin query language.

        Azure Cosmos DB

        On Microsoft Azure, this is a multimodal database that includes graph database functionality that supports the Apache Gremlin API by incorporating most Apache TinkerPop functionality.

        Amazon Neptune

        On Amazon Web Services (AWS), this is a fully managed Graph Database service.

        There are not as many choices on each platform for Graph Databases as there are for other Application Databases. This means that your application might need internal code to address features that are not available on the platform databases.

        Ecommerce Product Recommendations and Graph Databases

        Users of ecommerce sites are probably familiar with the section below the particular item you are browsing titled “similar items” or “purchased together with.” This is the result of a product recommender system, and once you start looking for them, you will find them everywhere. Amazon and other shopping websites typically recommend other products that fit well with this product. A recommender system is famously part of Netflix, which held annual contests to improve its recommendation algorithms. It is the basis of systems like Spotify, which is essentially only a big recommendation engine.

        But what is a recommendation engine? At its heart, it’s an exercise in data science and linear algebra. It usually comes down to constructing vectors for which you can calculate cosine similarity showing how close two or more items are to each other in that vector space. But how do you even construct those vectors? Where do the numbers in this data science exercise come from? That’s where a Graph Database comes in and excels.

        In a common implementation, whenever a user interacts with a system—purchasing a product, filling a cart, or even browsing a page—the system records that interaction as nodes and edges in a Graph Database. So if a user buys two products, edges are created between the user node and the product nodes. That could allow your analytics system to traverse those edges later and find that the user had purchased the two products, and use that information to recommend the second product to someone who is browsing the first.

        More accurately, the recommendation system would construct vectors from the records of the interactions of hundreds or thousands of users, each adding their own information to strengthen specific connections between the nodes (incrementing use counts), and then use the magic of linear algebra to find those products for which the connections are the strongest.

        When you throw in individual user interactions and their own preferences, this can give you highly accurate and personalized recommendations.
        """,
    "Columnar Database":
        """
        Columnar Database

        You are writing a Cloud Application or Microservice structured

        with a Cloud-Native Architecture and are selecting an

        Application Database for your application to use to persist its domain data.

        How can an application most efficiently store data for performing analytics, such as in a data warehouse?

        Often an application needs to store data that it uses to calculate statistics or perform Aggregate queries. This is especially

        common in Microservices Architecture (Chapter 4) when one Microservice pulls together data from several Microservices to perform queries or Aggregate data.

        An interactive user application requires online transaction

        processing (OLTP), and Relational Databases perform OLTP well. A user fills out a form, and the database writes the fields from the form to a database table. As multiple users also fill out that form, each user’s answers are written to a row in the table using a transaction for each user. The answers are all the same format because they all come from the same form, so the database table’s strongly typed schema handles it well. When a user wants to see the form with the data they previously filled out, that database read is a transaction. The application can use a couple of transactions to show the user their data, let the user edit the data, and commit the changes. Similarly, for data that is

        not as well structured, a Document Database can perform transactions on individual documents.

        In these OLTP scenarios, a read or write transaction involves an entire table row, using all of the data in that record. The application can query to find the rows that it needs, then reads or updates all of the data in those rows. Relational Databases do this well because they are optimized to manage data as complete table rows. OLTP requires both inserting data into the database as well as reading it back out again. Relational Databases tend to be equally good at both, providing reasonable performance.

        Data analytics requires online analytical processing (OLAP). When a Relational Database tries to perform OLAP, it becomes a performance bottleneck, limiting how much data can be processed quickly and not scaling well even with additional hardware. Data analytics requires sorting through large amounts of data and finding interesting data quickly. A Relational Database tends to approach the problem by reading all of the data from disk and iterating through it linearly, which doesn’t scale well. Analytics often is not interested in much of the data in a record, focusing more on knowing which records or how many total match a search. Analytics needs a database that can query data as efficiently as possible, even if that hurts the performance of inserting and updating data. While an OLTP database can efficiently insert and update individual records, this is uncommon in OLAP databases. An analytics database often loads data in bulk, writing the data in large batches, not one record at a time as with OLTP. Analytics data is typically loaded once and then read repeatedly, as the data is analyzed and reanalyzed for different purposes.

        Analytics data often isn’t as well-structured as OLTP data. The data to be analyzed can be gathered from multiple places that collect varying details about each record. Force-fitting the semi-structured data into a strongly typed schema will at best make the database table sparsely populated and at worst force the application to throw away data fields that don’t fit into the schema.

        OLAP needs a database optimized for reading and sorting through large amounts of data, even if that means its performance suffers when writing individual records, and that can still organize semi-structured data for efficient querying.

        Therefore,

        Store the data for an application that performs analytics in a Columnar Database, a database optimized to find records quickly, even in semi-structured data.

        A Columnar Database is often described as NoSQL but more precisely is schemaless or wide-column but still based on tables. Columnar Databases support very rapid SQL-style querying of large amounts of semi-structured data, rows of data that the

        database organizes into columns. It is typically a Replicated

        Database that runs in multiple nodes, storing its data in one or more keyspaces that it replicates across multiple nodes.

        Figure 7-20 shows a Columnar Database running in three database nodes that store records in three keyspaces with two replicas of each keyspace. The database can route each client request to any of its nodes. If a node receives a request for a keyspace it does not store, it reroutes the request to another node that does store the keyspace.





        Figure 7-20. Columnar Database True to its name, a Columnar Database stores data not in rows but in columns. For example, consider a table that stores the first names, last names, and zip codes for a set of customers. A standard Relational Database would store each row separately as a record written to disk, the data for one row all together on disk, followed by another. Instead, a Columnar Database stores each column separately as a record written to disk, the data for one column with the values for all rows all together on disk,

        followed by another. Figure 7-21 shows the difference.





        Figure 7-21. Column orientation

        This differentiation may seem trivial, but when querying large data sets to look for certain column values, this arrangement of the data makes the database much more efficient.

        A major disadvantage of a Columnar Database is that updates and inserts may take much longer than in other types of application databases. An application still inserts data records by row, but the database does not insert a single row. Instead, the database must break the row into columns and insert its values into each of the columns, writing the new column data to the same area of the disk as the existing column data to keep it all contiguous. OLTP applications perform a lot of inserts of individual records and therefore will work better with a Relational Database or a Document Database. Once an OLAP application inserts or updates data, it then reads it many times, making read efficiency a higher impact than write efficiency. When an OLAP application does insert records, it tends to load the records in bulk, so the database can perform the insert overhead once for all of the records. When data is needed for both OLTP for user interactions and OLAP for analytics, an application can store it twice in two different databases, where the application continuously updates the OLTP database but queues the updates for the OLAP database to perform them in bulk as a batch job.

        Understanding how a Columnar Database is able to query data so much more efficiently than a Relational Databases requires understanding how the Columnar Database is implemented and how it organizes its data. A Columnar Database groups entities that will be searched together, splits up rows to store the data by column, skips empty column values, and compresses data for reading from disk faster.

        A common Columnar Database implementation groups its data into keyspaces containing column families. A column family stores records that externally seem like rows of data with a UID for the record and a tag on each column value that specifies the column. The column tags enable records in the same column family to specify different columns. This makes each column family act somewhat like a Relational Database table and each keyspace act like a schema (i.e., a collection of tables).

        Figure 7-22 shows a keyspace with column families for two different entity types. The database performs each search in a column family, essentially by retrieving a column in that column family, so the application should put data that should be searched together in the same column family. Each record in a column family needs a UID, so if two records somehow have the same UID, they need to be put into two different column families.



        Figure 7-22. Columnar Database keyspaces Although all of an application’s data can be stored in a single column family, a good approach typically is to store each type of entity in its own column family, such as customers in one column family and products in another, which enables the entity types to be searched separately.

        While an application still externally inserts data records by row, the database internally stores the data by columns, as

        shown in Figure 7-23. The database can more efficiently read a set of column values from one contiguous section of disk and reads only the data for that column, making the amount of disk to be read minimal and the amount of RAM needed to load the data smaller. Then the database can search that smaller amount of RAM more efficiently to develop statistics about the data. Many OLAP use cases are multidimensional, with each dimension being a column. Arranging the data by columns enables the database to read only the data in the dimensions’ columns and then quickly find their intersection.





        Figure 7-23. Columnar Database columns

        For an example of how storing data by column makes querying more efficient, consider looking up how many customers live in a particular zip code. A Relational Database would need to iterate through all of the customer records, filtering for the ones with the particular zip code, and then would return all of the data for all of those records just to compute a count of the number of records. Even by optimizing the database with indexing and performing the count in the database instead of the application, a Relational Database cannot perform this search as efficiently as a Columnar Database. A Columnar Database instead would store a column of zip codes and could quickly find how many of those match the particular zip code. It might even optimize the column to list each unique zip code once and, for each unique zip code, list the rows with that zip code, which makes searching for a particular zip code as instantaneous as finding that one value from that one column.

        A Columnar Database can compress data, which enables it to perform queries even faster. Compressing the data stores it using less disk space, which makes it faster to read and allows more data to be loaded into the same amount of RAM. To accomplish this compression, rather than storing all rows in a column, the database stores only the rows that have values for

        that column, as shown in Figure 7-23. The shorter the column, the more compact its data is, with no loss of data. For example, the zip code column does not store data for all customers it only stores data for customers with zip codes, making it more compact. If a customer does not include a zip code, its data is stored in other columns but not in the zip code column. Columns are also more efficient to store because all of the values in a column have the same type so the database can store them with no wasted disk space. As mentioned earlier, the database can compress the column further by listing each unique column value only once and then listing the IDs for the customers with that value, which for a lengthy column value saves more disk space as well as makes a query for that value more direct.

        While the structure of data in a Columnar Database is more flexible and can seem semi-structured compared to the well-structured data in a Relational Database, Columnar Database data still needs structure. A Columnar Database can work efficiently as a wide-column database, storing records where most of the columns are blank. In a Relational Database, all of the missing values would produce very sparsely populated

        tables, as shown in Figure 7-24.





        Figure 7-24. Columnar Database column families as tables

        Since a Columnar Database stores only the columns that have values, it stores the data with high density. Yet while columns can vary between records, the data needs enough structure that it can be searched effectively, which means the records require the important columns that the application will search. The Columnar Database doesn’t force two records with the same data type to store both in the same column, but if they have different column names, they will be very difficult to search. When data has very little structure, where every record has different columns, the database will store that data in a huge range of columns with very few rows per column, which will be very difficult to search. For example, Column Family B in

        Figure 7-24 will be very difficult to search effectively since none of the rows have the same column, so any column value matches at most one row.

        Although a Columnar Database is often characterized as a NoSQL database, that perspective is misleading. A Columnar Database can appear somewhat schemaless because it can act as a wide-column database where each record populates only some columns. Yet it still has a schema, albeit not a predefined fixed schema but one the database determines dynamically to include numerous columns as needed. Whereas NoSQL Document Databases and Key-Value Databases work well with semi-structured and unstructured data, a Columnar Database needs data to have enough structure that it can be queried effectively. Many Columnar Databases store their data in Relational Databases, which are definitely not NoSQL. And unlike a NoSQL database, many Columnar Databases can still be queried with SQL and can be ACID compliant—even though their inserts are slow, they are consistent. In this situation, you can think of a Columnar Database as an SQL database with a dynamic wide-column schema.

        A Columnar Database manages data for OLAP, optimizing data storage for query efficiency at the expense of performance for inserting and updating data. It organizes data records into columns to make it more efficient to query. It can handle semi-structured data, although the data has to be structured well enough for efficient querying.

        Analytics focuses on finding a small amount of interesting data within a large amount of data. Columnar Databases make it possible to do this much more efficiently.

        However there are some challenges, such as limited suitability for transactional workloads, higher overhead for writing data, and complexity in handling joins. Also, they can be resource intensive for small queries with increased complexity for certain operations. Finally, there can be a learning curve along with scalability and concurrency challenges.

        For OLTP, use a Relational Database or Document Database .

        Each keyspace in a Columnar Database is a Data Module . Use

        Polyglot Persistence to store Data Modules for OLAP in a columnar database and Data Modules for OLTP in relational and document databases.

        A Columnar Database should be hosted by the cloud platform as

        a Database-as-a-Service . Most public cloud platforms host at least one columnar DBaaS.

        Examples

        Here are some common examples of Columnar Database products and public cloud platform services, as well as a domain-specific example implementing marketing using an airline application.

        Columnar Database products, projects, and services

        These products and open source projects implement Columnar Databases:

        Apache HBase

        An open source, column-oriented, distributed, versioned, non-relational NoSQL database modeled after Google’s Bigtable. Contributed by Yahoo as part of Hadoop, HBase stores its data in the Apache Hadoop Distributed File System (HDFS) or Amazon’s Simple Storage Service (S3) and is designed to support real-time read and write access to large data sets.

        Apache Cassandra

        A distributed NoSQL database contributed by Facebook that uses a column-oriented storage model and is designed to handle large amounts of unstructured or semi-structured data.

        ScyllaDB

        An open source wide-column database designed to be API compatible with Apache Cassandra while offering significantly higher throughput and lower latency.

        IBM Db2 Warehouse

        A column-organized data warehouse with in-memory processing designed for complex analytics and extreme concurrency.

        These cloud platform services provide Columnar Databases (DBaaSs):

        IBM Db2 Warehouse on Cloud

        Supports columnar storage and is hosted on IBM Cloud using IBM Cloud Object Storage and on AWS using Amazon Elastic Block Store (EBS) with Amazon Elastic File System (EFS).

        Google Cloud Bigtable

        A hosted distributed NoSQL HBase–compatible database that runs on top of Google File System (GFS), is designed to support real-time read and write access to large data sets, and is integrated with the Google Cloud Data Platform. Google describes it as “a sparse, distributed, persistent multidimensional sorted map.”

        Amazon Redshift

        A hosted petabyte-scale massively parallel processing (MPP) cloud data warehouse service with columnar storage designed to handle large-scale, high-performance data storage and analysis needs for applications on AWS.

        Amazon Keyspaces

        A hosted, scalable, and highly available database service that supports the Cassandra Query Language (CQL) API.

        Azure HDInsight HBase

        Apache HBase hosted in a managed cluster using Azure Storage.

        When choosing a Columnar Database, an important factor is compatibility with other parts of your analytics toolkit. You want to ensure, for instance, that your reporting tools are compatible with your Columnar Database when making your product selection.

        Airline marketing example and Columnar Databases

        Marketers often want to target a promotional offer to existing customers who are likely to be interested. To do so, they search through a sea of historical data about lots of customers’ purchases to look for activities similar to the new offer, reasoning that customers who have made purchases like this in the past may be interested in doing so again. This searching through historical data and looking for interesting patterns is data analytics, and Columnar Databases are especially good at performing OLAP. Other types of databases are tuned for OLTP, which provide poor performance for analytics, but Columnar Databases are optimized for analytics to provide much better performance.

        For example, let’s consider an airline that is running a route to San Francisco from Chicago. To drum up more business for this route, a marketer with the airline may wish to find customers who might be interested in this route and offer them a special promotion. To find these customers, the marketer runs a query on the airline’s historical data along the lines of “Find all frequent fliers who purchased flights leaving Chicago where the yearly spend was over $100,000 in the last year.” This is a very complex query: it needs to filter for customers who are frequent fliers, have departed from Chicago, have spent a lot on flights, and have done so in a limited time frame. A Relational Database might contain the data for all customer flights flown in the past several years, and running SQL across that much data would require a lot of I/O that reads a huge amount of disk. The data needs to be filtered in multiple independent ways— frequent fliers, Chicago departures, high spenders, recent activity—and each filtering process will consume considerable memory and CPU. Ultimately, the filtering will throw away data that never needed to be read in the first place. When the querying finally produces a list, the marketer may find it contains too many names or too few, necessitating adjusting the query and running it all over again!

        A Columnar Database is optimized to run multidimensional queries across huge sets of data and read only the data that is needed. If the data for all flights flown in the past few years is stored in a columnar database, the database will perform this marketing search much better. It will have a much easier time producing a list of customer IDs for frequent fliers, for fliers with Chicago departures, and for fliers who are high spenders based only on their activity for the past year, than producing the intersection for all three. Using a columnar database, the marketer will get their results much faster, placing much less load on the infrastructure because it reads much less data from the disk—only the customer IDs from the desired columns. They can look at the number of customer IDs and judge whether that’s a meaningful number without reading all of the customer records. They can more quickly adjust their query to find a meaningful list, even if that means running queries multiple times to find one that works best.

        With that list of customers who are likely to be interested, the marketer can then recommend to those fliers that a vacation in San Francisco would be a great idea!
        """,
    "Data Module":
        """
        Data Module

        You’re developing an application with a Cloud-Native

        Architecture that has domain data and needs to persist it.

        Perhaps you’re developing a Self-Managed Data Store for a

        Microservice .

        How can I align my data model with my application model so that both are easier to maintain and can evolve quickly?

        An enterprise application often stores all of its data in a single large Relational Database. Furthermore, in many enterprises, the majority of the enterprise applications share one huge set of data stored in one or a few enterprise databases of record. Even when an application has some data that none of the others will use, it stores that data in the same enterprise databases of record because that’s where all of the applications store all of their data.

        An enterprise database of record is difficult to maintain. No one application is responsible for any set of data; it is shared by many applications, and they are all responsible for it. Some of it may not even be used anymore—the applications that once used it have changed, yet it still remains in storage. If one application corrupts the data, all of the other applications that use the data are adversely affected, all assuming the data is valid and having no way to determine which application introduced the problem. Once data is stored in a certain schema, that schema cannot be changed because multiple applications share the data, and they would all need to be updated to the new schema at the same time that the database is updated. Thus, an enterprise database of record becomes an ever-growing warehouse of data, much of which is never used, stored in a schema that may no longer be ideal and that the enterprise has no ability to improve.

        Data is often convenient to store in an enterprise database so that any data can be referenced and connected to any other data. Referencing data in separate databases is difficult, but doing so in the same database is easy, and the database can maintain referential integrity. Yet the more connected data is, the more difficult it is to change. Schema is already difficult to change in a shared database. Connections between sets of data create dependencies such that changes to some of the data, even without changing the schema, impact other data such that it may also need to be updated.

        Large sets of interconnected data make the data more difficult to maintain and much slower to evolve.

        Therefore,

        Divide the application’s total set of data into Data Modules, sets of data with no or limited dependencies with one another, and store each in its own database or schema.

        Data Modules divide a large set of data into smaller sets of data. The data inside a module is closely related, whereas the data in one module is more loosely related to the data in another module. While one database can store multiple modules, to maintain their independence, each module should be stored in its own database (aka schema or set of tables). Each database can be hosted in its own database server, but it can be more efficient to consolidate multiple databases into one database server.

        Figure 7-25 shows the set of data for an application divided into four modules. Each module includes multiple data types that together implement an encapsulated unit of data. The data in one module can reference the data in another module, but most of the references are within a module with relatively few references between modules.





        Figure 7-25. Data Module

        Data Module is the data version of the Modular Monolith and

        Distributed Architecture patterns for applications. Just as an

        application is more difficult to maintain as a Big Ball of Mud , dividing data into modules and storing them in separate databases makes the data easier to maintain.

        Applications and modules should connect only to the databases with the Data Modules that the code uses. Each application in an enterprise should not connect to all of the Data Module databases in the enterprise; they should only connect to the ones whose data it uses. This approach leads to fewer applications connecting to a given module’s database, making that data easier to maintain and evolve. For applications with a Modular Monolith architecture or Distributed Architecture, each module should only connect to the databases of the data it uses.

        The modularity of the data should reflect the modularity of the application so that each application module typically uses a single data module. This alignment between application modules and Data Modules becomes especially apparent in an application with a Microservices architecture. Each Microservice manages its own data, which is a data module, and

        stores it in its own Self-Managed Data Store , which is the database that hosts the Data Module. Each Microservice has its

        own database, as shown in Figure 7-26.





        Figure 7-26. Schema per service

        Figure 7-26 also shows that the databases for multiple Microservices can all be hosted in a single database server. A single server enables multiple Data Module databases to share the server’s infrastructure resources, administration effort, and licensing costs. Each Microservice owns its data and stores it in a separate Data Module it controls, yet shares the overhead of the database server. Each Microservice owning its Data Module helps developers avoid coupling their microservices and the database (either intentionally or unintentionally). To enforce this, configure each Microservice so that it can connect only to its database, and vice versa.

        A data model with a good design groups data into well-organized modules. At one extreme, every data type could be stored separately in its own module. At the other extreme, all data types could be stored in a single module. Here are some guidelines for figuring out a good set of modules:

        If one logical data type is normalized across multiple tables,

        those tables should all be hosted in the same module.

        If two data types need to be updated in a single transaction,

        they should be hosted in the same module.

        If two data types have the same lifecycle, such that when the

        record is created or deleted, records for the other data types

        should be created or deleted as well, put them in the same

        module.

        If two data types have very different lifecycles, such that one

        is still viable after another is deleted, host them in separate

        modules.

        If one data type is shared by two other data types, host them

        in separate modules.

        For an enterprise with an enterprise database of record, refactoring the application into modules may be much easier than refactoring the database. The application has limited scope, whereas a database that is used by multiple applications cannot be changed without also changing all of the applications. These constraints often result in a set of Microservices that all share the single enterprise database just like the other enterprise applications do. Ideally, the Microservices should each have their own database, and they may be able to do that for new Data Modules, but when the existing data is all one big module, multiple Microservices will have to share it as is.

        Data that will be modified together should be stored in the same data module so that it can be modified in the same transaction, but that creates a quandary when two different sets of data need to be modified together. Two different Microservices should store their data in separate Data Modules in separate databases, but then two sets cannot be modified in a single transaction. This situation may require connecting together the

        two Microservices through Service Orchestrator or Event

        Choreography . Then when one Microservice updates its data, it invokes or notifies the other Microservice so that it can update its data as well.



        Data Modules enable making data as modular as the application. Data that is updated together should go in the same module; data that is merely used together can go in separate modules. Each module should be hosted in a separate database, and multiple databases can be hosted in the same database server. Application modules should connect only to the data modules with the data they use.

        An enterprise database of record can be much more difficult to refactor than an application. A database may be shared by multiple applications, which would require updating all of those applications when the database is updated. And data all stored in one database may be highly intertwined and difficult to separate.

        Store each Data Module in its own separate database, which is

        an Application Database .

        Since each application database is separate, data in two Data Modules do not have to be stored in the same type of

        application database. For each Data Module, use Polyglot

        Persistence to choose the type of application database that works best for the data in that module.

        Multiple Data Module databases can be stored in the same database server. On a cloud platform, that database server can

        be hosted as an SaaS service, an instance of a Database-as-a-

        Service .

        Examples

        Let’s explore what different types of databases and database products call the construct for dividing the server into databases for separate Data Modules. Then we’ll look at a simple example of an ecommerce application that uses multiple Data Modules. Finally, we’ll consider a quick example of refactoring a monolith with one large database into

        Microservices that each have their own database, all hosted in a single database server.

        Database server terminology for hosting multiple databases

        Most database servers have a construct for dividing the server into databases for separate Data Modules, but different types of databases and database products have different names for that construct. Many NoSQL databases advertise themselves as being “schemaless.” but the general concept of a boundary of separation that a Relational Database schema provides is also provided in those databases. However, exactly what it is called differs from database to database and (unfortunately) is often tied up in the details of the clustering and management structure of each database. Nonetheless, we can point to a

        single concept in most Application Databases that represents a distinct set of data and a description of the structure of that

        data that acts as a single Self-Managed Data Store that the operations of a single Domain Microservice can operate on. Here are a couple of different types of databases and the feature in each that represents a Data Module:

        PostgreSQL schema

        In PostgreSQL, a schema is a collection of tables that represents a single logical database. PostgreSQL also has a concept it calls a database, which is a collection of schemas tied together by a common set of users. Of these two concepts, schema aligns most closely with Data Module.

        MongoDB collection

        In MongoDB, a collection is a set of documents. That collection represents both a scope for searching documents and also the mechanism for finding the structure of the documents. Thus each Data Module stored in MongoDB should be stored in its own collection. MongoDB does not require that all the documents in a collection fit the same schema, but when a collection has schema validation enabled, MongoDB validates the format of data during updates and inserts it into that collection.

        Apache Cassandra keyspace

        In Cassandra, a keyspace is a collection of tables and types tied to a replication strategy. Store each Cassandra Data Module in a separate keyspace.

        Neo4j Graph Database

        In Neo4j Graph Database, the best equivalent to a Data Module is the database, which is a single connected graph made of nodes, their properties, and the relationships that tie them together. A single Neo4J installation can host multiple databases (at least in the Enterprise Edition of Neo4J).

        Redis shard key

        Redis is the most difficult choice in which to implement this concept. In Redis, there is no single built-in concept within the database API that directly corresponds to a Data Module. Redis partitions by sharding the key, so to store data in Data Module, construct keys that include a unique identifier for each module.

        Likewise, other database products and services have their constructs for organizing Data Module as sets of data. Ecommerce application

        An ecommerce application keeps track of customers who order

        products. Figure 7-27 shows a potential modularized Data Module for the application.





        Figure 7-27. Ecommerce Data Modules

        This Data Module separates the data into modules for customers, products, and orders. While customer seems like a single type of data, each customer also has closely related data, like their mailing addresses as well as the customer’s preferences. Likewise, the data for a product also includes pricing data that tends to change independently of the product, and each product can have multiple customer reviews. Order brings these two units together, relating a customer to the products they ordered. A separate order data type enables one customer to have multiple orders and for multiple customers to order the same product. Even Order contains more than one type of data. Orders must track the status of the order as it shifts through its lifecycle and the details of the shipping process that also has its own lifecycle.

        Refactoring a Big Ball of Mud and its database into Microservices with Data Modules

        Let’s say that you are currently using a single, large Relational Database. In that case, problems arise when you have two different Microservices that use the same information—the same tables within the same schema. The problem is that when everything references everything else, it is difficult to figure out

        how to split them apart. You see what we mean in Figure 7-28.



        Figure 7-28. Monolithic Application working off One Big Schema



        As you transition to Microservices, you must realize that there are many fewer problems caused by sharing hardware at the server level—in fact, when doing the initial refactoring to Microservices, there are a lot of advantages to keeping the new, more cleanly separated schemas in the same enterprise servers because companies usually already have teams and procedures in place for database backup and restore, and for database server updates—which the teams can take advantage of. In a sense, what the enterprise is providing through providing the hardware and software and management of an enterprise

        database is a limited version of a Database-as-a-Service . This especially fits well with an approach that begins with more cleanly separating parts of your monolith by functional area—

        starting out with a Modular Monolith, as shown in Figure 7-29.





        Figure 7-29. Schema per module

        In this example (meant to show a refactoring work-in-progress). you can see how the database has been broken up by separating out tables corresponding to three new schemas (A, B, and C) that correspond to specific modules in the refactored application. Once they have been separated like this, they can be cleanly broken out into distinct Microservices. However, D and E are still being refactored—they still share a single schema with interconnected tables.

        You can easily see how this is a step toward the desired end state of a set of microservices that each manage their own data.
        """,
    "Polyglot Persistence":
        """
        Polyglot Persistence

        You’re designing an Application Database for an application to

        store its Data Modules . There are many types of Application Databases to choose from.

        How can an application store its Data Modules in the type of database that works best for the application’s data structure and how it accesses the data?

        When all of the applications in an enterprise share the same enterprise database of record, choosing what database to use is simple: always use the enterprise database of record; it’s the only choice. Furthermore, selecting the database technology for hosting the database is simple because it is always a Relational Database. The only real decision is whether to use Oracle, Db2, or SQL Server, and usually the enterprise has already standardized on one of those long ago. So for any application with some data to store, the decision is simple: store the data in the enterprise database of record which is a Relational Database hosted in the database product the enterprise has always used.

        Cloud and distributed architectures have motivated innovation in database technologies, resulting in numerous database products and open source projects to choose from, implementing several types of Application Databases. While an application has many databases to choose from, it’s not clear

        which one it should choose. Relational Databases have many

        advantages and disadvantages compared to Document

        Databases , while Key-Value Databases excel at some tasks but not others, and so on for the other database types. An application can treat all of its data like table data, but that may not work very well for some of the data.

        Even with multiple database types and database products to choose from, an enterprise may feel compelled to standardize on one product. One product shares licensing costs across more data and makes staffing projects easier when all of the developers have skills in the same database. Yet uniformity for licensing and developer skills may stifle the opportunity for each application to use the best database for its requirements.

        An application works better if it is modularized into a Modular

        Monolith or Distributed Architecture such as Microservices . Likewise, the application will have more flexibility if it modularizes its data model into Data Modules. If the application has modularized its data, to standardize on one database, it needs to store all of its Data Modules in the same database, such as storing them all in a Relational Database or all of them in a document database. For an application with diverse sets of data, any database choice will work well for some data, but another database choice would work better for other data.

        What is needed is a database that is optimized for each module in the data model. Yet no one database is going to work best for every module.

        Therefore,

        Use Polyglot Persistence to store each data module in the type of database that works best for that module.

        Polyglot Persistence stores each Data Module not just in a separate database but also in a different type of database. Some modules may happen to use the same type of database, not because they all need to be stored in the same type but because that type is the best choice for each of them. If two application modules both use table data, they should store both of their Data Modules in Relational Databases. But if one of them uses semi-structured data, it should store its Data Module in a Document Database even though the other module uses a Relational Database. Polyglot Persistence gives this flexibility.

        Figure 7-30 shows an application split into three modules that split its data into three Data Modules. While all three Data Modules could be stored in the same type of database, the application modules have different types of data that can be managed better by different database types, and Polyglot Persistence enables the design to store each Data Module in a different database type. The first module has well-structured data, so its Data Module works best in a Relational Database. The semi-structured data in the second application module means its module of data stores most easily in a Document Database. The third application module uses a Key-Value Database because its data is unstructured. With Polyglot Persistence, the design stores each Data Module in the database type that works best for that data.

        Polyglot Persistence is the data version of Polyglot Development . Just as two different Microservices can be implemented in the same language but do not have to be, two Data Modules can be stored in the same database type but do not have to be. Polyglot creates the opportunity not only to implement two Microservices in two different languages but also to store two Data Modules in two different types of databases. Since two Data Modules should be stored in two separate databases anyway, when needed, those two databases can be of two different types.

        Polyglot Persistence supports storing Data Modules in separate database servers but does not require it. When a designer chooses to store two Data Modules in the same database type, they can be hosted in two different databases within the same database server. To host two data modules in two different database types, the two databases must be hosted in two different database servers.





        Figure 7-30. Polyglot Persistence

        While providing multiple database types gives applications flexibility in persisting data, supporting them may introduce complexity. Each new type means hosting new database servers, and servers of different types mean that a team will need database administrators and application developers with skills to handle multiple types.



        Polyglot Persistence enables storing each Data Module in a different database type but does not require it. It enables development teams to choose the best database type for each Data Module. Data Modules that store their data in the same database type can be hosted in the same database server.

        Multiple database types mean hosting and administering multiple database servers of different types, skills, and costs that can increase application complexity.

        Each database type is easier to host and administer if it is a

        Database-as-a-Service .

        Example

        Let’s revisit our earlier example drawn from a simple ecommerce application consisting of a few easily understood

        Domain Microservices and consider the different types of Data Modules and thus Application Databases that would be found in this application:

        Catalog

        Enables the user to browse information on different products, see descriptions, view images of the item, and find out the price of the item.

        Shopping Cart

        Enables the user to select items from the catalog and then store them for later purchase.

        Product Recommendations

        Helps the user have a better shopping experience.

        Order

        Once you have passed through the purchasing process, including arranging for payment and shipping, the

        order must be fulfilled

        Each of these different Microservices requires different types of data, each of which may fit a different set of storage

        requirements, and thus a different type of Application Database , for example:

        The Catalog is a perfect example of document data. Each

        catalog entry is a mix of different fields with different types

        of data in each, and what’s more, the set of information may

        differ from product to product. (For example, there are more

        things to describe in a complex item like a car than in a

        screwdriver.) A Document Database enables flexible data

        formats, efficient searching, and support for returning

        multiple data types to the frontend as individual JSON

        documents.

        The Purchase button will need to take the shopper through

        multiple screens (get shipping address, get credit card

        information, confirm the purchase, etc.), which requires

        them to move back and forth between the screens. This

        session data can easily be cached in a Key-Value Database .

        Product Recommendations require fast navigation

        through lots of different types of data, stored

        multidimensionally: what the user has purchased before,

        what other users similar to them have purchased, their

        demographic data, etc. A Graph Database is exactly the right

        solution for navigating this data.

        The Shopping Cart allows for multiple possible solutions,

        such as a Document Database or a Key-Value Database. Either

        way, the Shopping Cart data is its own Data Module that

        separates the data for the Shopping Cart Microservice

        from the Data Modules for the catalog Microservice or

        purchase Microservice.

        Once an Order has been created from a Shopping Cart ,

        the order fulfillment, packing, and shipping process often

        involves lots of small changes to distinct parts of the original

        order (for instance, items may be shipped separately or in

        small groups and also returned separately). That kind of

        searching and updating of small pieces of information is

        perfect for a Relational Database .

        As previously described, Polyglot Persistence is a necessary tool to solve the problem of optimizing each Microservice to address its own unique set of problems in the domain. For more information on each of the different specific use cases for this example, see the corresponding examples in each of the individual patterns.
        """,
    "Database-as-a-Service":
        """
        Database-as-a-Service

        You’re designing an Application Database to store the data for

        your Cloud Application .

        How does an application have access to an Application Database?

        An enterprise database of record is not optimized for applications to persist data; it is optimized for database administration. When an enterprise wants a new database, or even a new table in an existing database, the developers submit a request to the database administrator (DBA) team. The DBAs specialize in database management—such as creating backups, restoring backups, normalizing and optimizing schema, and software licensing—which relieves development teams of these responsibilities.

        In their request to the DBAs, the developers must justify the need for yet another database or tables and specify details like the schema, how much data will be stored, and how it will be queried, details developers often do not know early in a project. The DBAs limit the number of databases because a few big databases are easier to manage than many smaller ones. Keeping track of which applications need access to which databases is easier when all applications have access to all databases. Assigning a database a large but limited amount of storage up front makes storage easier to manage.

        Database administrators and enterprise databases become an

        impediment to agile development, especially of Microservices .

        Each Microservice should have its own Self-Managed Data Store

        to store its data as a Data Module in its own database. The team that develops the Microservice should also be responsible for its database, creating a database when needed and controlling how it stores the Microservice’s data.

        Creating a database isn’t simple and could require a whole new set of skills for the development team. The team needs to provision a set of bare metal servers or virtual servers (aka virtual machines (VMs)), as well as a set of block storage. The team then needs to download the database software, install it on those servers, and configure it with software licenses and to perform backups. All of this requires database administration skills a developer may not normally have, and these skills differ for each database product.

        Since a Microservice is a Replicable Application , it can scale

        linearly, which means its database needs to be a Replicated

        Database so that it can scale linearly as well. A replicated database is more difficult to install, if for no other reason than because it requires provisioning multiple servers and installing the database software on each of them.

        Since the developers are using a cloud platform, rather than the development team having to install and administer its own database, a service the cloud could provide is to already have databases installed for development teams to use.

        Therefore,

        Create your Application Database by using a Database-as-a-Service, a cloud service that handles much of the work of installing and managing a database.

        A Database-as-a-Service (DBaaS) is a software-as-a-service (SaaS) in the cloud. Whether the service is built into the cloud platform, loaded onto the cloud platform, or accessed remotely as a web service hosted by a vendor in their data center, the

        application accesses a database in the service as a Backend

        Service . The service manages a set of database servers and installs databases by hosting them in those servers. The service simplifies creating databases in those servers, handles the licensing, and simplifies management tasks like scheduling backups. Developers can easily create a database and set it up with schemas and other database configurations to store the application’s data.

        Figure 7-31 shows three Cloud Applications that each has its own cloud database. All three cloud databases are hosted by the same DBaaS. Each DBaaS is for a particular database product, so this single DBaaS assumes that all three databases are instances of the same product, such as all PostgreSQL or all MongoDB. Applications that need two different database products, like a PostgreSQL database and a MongoDB database, will need a DBaaS for each.





        Figure 7-31. Database-as-a-Service

        While developers have a range of application database products to choose from, they are limited to the DBaaS services available on their platform. The easiest ones to use are ones built into the cloud platform as SaaS services. A second option is databases that can be downloaded from a marketplace, such as the

        Kubernetes operators in OperatorHub and Red Hat

        Marketplace. Much like the cloud platform, the operator both installs the database service and manages it. A third option is database services hosted by the vendors in their own data centers and made available remotely as web services. If a development team wishes to use a database that is not made available via one of these three methods, the development team is back to having to manually download, install, and manage the database.

        A problem with development teams creating and using their own databases is that application developers may not have the skills to administer databases. Database administrators (DBAs)

        have more practice performing database tuning, Relational

        Database works better with optimized table normalization and

        indexing. A Document Database works better when the granularity of the documents is scoped to simplify data

        management. A Replicated Database works better when configured with customized partitioning and sharding policies.

        To help development teams administer their databases, a common solution is to form a dedicated team of experienced DBAs that the development teams share to tune their databases. DBaaS will free the DBAs from creating and managing databases so that the administrators can focus on configuring and optimizing the databases. The DBA team can also look for opportunities to optimize the usage of the database servers by hosting multiple databases in a shared set of DBaaS service instances. A skilled DBA team is most important for administering production databases. For other stages of the software development lifecycle (SDLC), such as dev and test, DBaaS databases with default settings may be adequate, requiring minimal administration or tuning.

        Finally, a last element to consider in using Database-as-a-Service are the security requirements of the data. In some cases, enterprises may prefer to keep data local rather than store it in the cloud, negating the ability of teams to use Database-as-a-Service. This may be due to regulatory requirements or merely to policy preference on the part of the company building the application. Regulatory issues are increasingly less of an issue since cloud providers have worked diligently to provide security features that are certified by regulatory agencies. However, there still may be cases such as those involving proprietary data (particularly when the cloud provider competes with the company using the provider’s services), in which avoiding the use a Database-as-a-Service may be a logical choice when made out of an abundance of caution.



        A Database-as-a-Service greatly simplifies creating and managing databases in the cloud. The service has already installed the database servers, handles licensing, and manages backups. Developers use the service to create a database and configure it to store the application’s data, which is much simpler than installing the database manually.

        Developers are limited to the DBaaS services the platform makes available. For any other options, the developers must manually install the database. Even with a DBaaS to create and manage databases, development teams may not have the skills to optimize databases and so can benefit from a dedicated DBA team to administer the application’s databases, particularly its production databases. Additionally, there can be vendor lock-in by a DBaaS provider, which may not allow your organization direct control over the servers executing the database. Often the cloud service DBaaS provider is in charge of monitoring the database platform and supporting infrastructure, which might lead to security or confidentiality concerns along with compliance or regulatory challenges.

        All of the types of Application Databases and Configuration Databases that we cover in this chapter can be hosted as a Database-as-a-Service. Rather than list them all individually here, we provide multiple examples of different DBaaSs of each type in the respective patterns.

        Examples

        There are literally dozens of examples (perhaps hundreds) of this kind of service on cloud platforms. Among some of the most popular are:

        Amazon Relational Database Service (RDS)

        A popular DBaaS offering in AWS that enables users to launch and manage a variety of Relational Database engines, including MySQL, PostgreSQL, Oracle, and others. Amazon RDS provides automated backups and point-in-time recovery and is designed to be easy to use. It supports read replicas for these databases, which improves the scaling characteristics and addresses many cases requiring horizontal scaling.

        Amazon DynamoDB

        An offering in AWS that enables users to create and manage a highly scalable, fast, and flexible NoSQL database that supports both document and key-value data models, and is designed to be highly available and durable.

        Azure Cosmos DB

        A DBaaS offering in Azure that enables users to create and manage a globally distributed, multimodel database. Cosmos DB supports multiple data models, including document, key-value, graph, and columnar, and is designed to be highly available, scalable, and low-latency.

        Google Cloud Bigtable

        A hosted distributed NoSQL database that supports real-time read and write access to large datasets.

        IBM Cloudant

        A document database that is available as an SaaS service on IBM Cloud and as a third-party web service.

        The choice of which DBaaS offering to use will depend on the specific requirements of the application, the availability of the services on the application’s cloud of choice, and the trade-offs between cost, performance, and features that are acceptable for the use case.
        """,
    "Command Query Responsibility Segregation (CQRS)":
        """
        Command Query Responsibility

        Segregation (CQRS)

        You are designing a Cloud Database to store the complex data

        structures for multiple Cloud Applications . The application must manage complex Aggregate object data that must be consistent during concurrent updates by multiple clients. The applications will independently modify these complex data structures while they also read the data.

        How do you optimize throughput for query and updates by multiple clients that have numerous cross-cutting views of the data?

        At its simplest, the way an application uses the data in a database can be pretty straightforward: the application CRUDs the data, which is to say that it creates, reads, updates, and deletes the data records in the database. The application writes the data with a particular format and reads it back in the same format. Some of the time it writes data and at other times it reads data, but it usually doesn’t read while it’s writing or try to update data while it’s reading that data. Each data item is a fairly flat record of primitives that maps easily to a row in a

        Relational Database or rows in normalized tables.

        Yet many real-world applications are more complex. Data structures are nested, parts are shared by multiple records, and relationships exist between seemingly independent entities. For example, the product catalog for an ecommerce application has many data elements for each product, some of which are relevant to multiple products, and products are often related. Applications employ complex domain logic to validate data changes, keep it consistent, and maintain referential integrity. That verification works for one client updating the data, but when multiple concurrent client threads update the data at the same time, the domain logic only verifies the changes in each thread and cannot detect conflicts between threads. The domain logic needs to be applied sequentially, making it a bottleneck that handles only one update thread at a time and

        does not support replication (see Replicable Application ).

        Another complexity is optimizing data access. To help maximize data throughput, database administrators often optimize a database mostly for reading or mostly for writing. This approach is difficult to apply to a database with data that is frequently updated and read, especially data that is read while it is being updated. For example, the product inventory in an ecommerce application is updated whenever items are added to the warehouse and whenever a new order is placed. Meanwhile, the inventory is simultaneously read as users browse products and update their shopping carts. Database tuning that makes the data easier to update makes it more difficult to read, and data must be locked during updates specifically to prevent other threads from reading it. Writing data updates tends to take priority, creating a bottleneck for reading data, one that replication doesn’t improve and actually makes worse by adding client threads accessing the database.

        Yet another complexity is that not all applications look at the same data the same way. The application for a buyer may need to view inventory data by geography, whereas the application for restocking inventory needs it organized by quantity. The application for shipping current orders is interested only in products that are currently for sale, whereas an application for browsing order history needs data for old products that were available in the past. Querying can find these different sets of data, but a query can run more efficiently if the data is organized for that query. Yet for data that will be used in many different ways, there is no one right way to organize it. Any approach for organizing the data will help in using it in some ways but hurt in others ways.

        What is needed is a database and an approach for organizing data that handles complex data structures, maintains validity throughout concurrent updates, and serves different views of the same data efficiently while the data is also being updated.

        Therefore,

        Store the data in a Command Query Responsibility Segregation solution that duplicates the data in two databases, one that clients use to update the data and another for clients to read the same data.

        Command Query Responsibility Segregation (CQRS) stores a set of data not in one single database but as two copies in a pair of databases: one for reading and another for updating. The solution keeps the two copies synchronized—whenever the data is updated in the write database, it is likewise updated in the read database. Clients using the data do not access either database directly. Instead, the solution presents clients with two separate APIs: one for making modifications to the data and another for retrieving data. Clients need to choose which API to use; a client that wants to read and write uses both APIs but uses them separately. The APIs segregate the querying activity from the updating activity, directing each to the read and write databases, respectively.

        Figure 7-32 shows the Command Query Responsibility Segregation solution as two segregated parts, a write solution

        and a read solution, connected by an Event Backbone . The solution implements two databases, one in each part, each of which stores a copy of the same data. There are many approaches for implementing the CQRS solution; this shows one very comprehensive design with all of the solution’s features clearly designated.

        The write solution manages the write database and the API that updating clients use to modify data in the write database. The write database is the database of record for the entire solution because it always contains the latest consistent copy of the data. Clients cannot access the write database directly. Rather, clients that want to update the data do so using the modify API. The write solution implements the API to encapsulate each update

        as a Command (Design Patterns, 1994). The command facade can pass the update commands directly to the write model, or it can optionally queue the update commands on a Command

        Bus (Enterprise Integration Patterns, 2003). In cases with relatively few simultaneous updates, the write model and its updates to the database of record can process commands as fast as the command facade creates them, so the command bus isn’t needed. In cases where the write solution has many clients simultaneously using the command facade to create update commands, queueing may be needed to help the write model manage concurrency by serializing the update commands on a queue and enabling the write model to throttle its consumption of update commands from the queue.





        Figure 7-32. Command Query Responsibility Segregation A write model updates the database much as any application would, using a domain model to enforce data validity. The write model performs the update commands serially, performing each command to update the data in the database of record. At the same time, the write model also creates an update event for the command and queues it on the event backbone. The write solution can optionally include a log of the changes made to the database of record. If it does, whenever the write model performs a command and publishes an update event notification, it also records the update history by logging the update to the change log.

        As the write model reads and performs commands, to enforce data validity, it needs to perform the commands sequentially and perform each command on the latest set of data from the previous commands. To do so, the write model can be implemented as a Singleton that reads commands one at a time, completing one before starting the next. This design enforces serialization but makes the write model a performance and availability bottleneck. To avoid the

        bottleneck, the write model should be replicable (see Replicable

        Application ), which then means it must also be stateless (see

        Stateless Application ). To perform each command statelessly, a write model replica must use a single database transaction to lock and read the data from the database of record, use the domain model to update the data with the new data from the command while maintaining validity, and write the valid data back to the database. This is how the write model is able to serialize updates that the clients make concurrently and preserve the validity of the data—even complex Aggregate objects—after each update.

        The read solution manages the read database and the API that querying clients use to query the data in the read database. The read database mirrors the write database, maintaining a replica of its data. Clients cannot access the read database directly. Rather, clients that want to query the data do so using the retrieve API. The read solution implements the API as a read model that queries the data from the query database, a read-only replica of the data in the database of record; encapsulates

        the results as Data Transfer Objects (Patterns of Enterprise

        Application Architecture, 2002) (DTOs); and returns the DTOs to the client. Meanwhile, the read solution keeps the data in the query database synchronized with the data in the database of record. An event processor reads the update notification events from the event backbone (that were published by the write model) and reacts to each event by updating the data in the query database. Only the event processor can update the query database; the read model and its clients treat the query database as read-only.

        CQRS is a complex solution to a complex problem that accomplishes a number of key goals:

        Serialize concurrent updates

        By serializing the database updates as a queue of commands, the write model performs multiple updates sequentially, even when they’re initiated concurrently by independent clients. Sequential updates are not a bottleneck because they are queued, so clients can queue updates as rapidly as they like. By performing updates one at a time, the write model uses the domain model to validate each update and resolve conflicts.

        Manage complex data structures

        The write model uses the domain model to organize a consistent set of complex data and map it to the database efficiently.

        Separate client workloads

        Clients updating the data and clients querying the data no longer conflict because they use separate databases. Locking to update the database of record does not block clients from retrieving data from the query database. Read clients can query concurrently because the database

        is read-only. Reading is only blocked by the event processor synchronizing the data from the database of record.

        Load distribution

        The client load of updating and querying data is distributed across two databases.

        Schema optimization

        The database of record can have a schema, storage strategy, and tuning optimized for inserting and modifying data. The query database can have a different schema and storage strategy and be tuned differently to optimize it for querying data as defined by the retrieve

        API. While both databases can be Relational Databases or

        Document Databases , the two databases can easily be two

        different types of Application Databases , such as a Key-

        Value Database to store primary copies of the data quickly

        and a Columnar Database for optimized querying. Try accomplishing that with any single database.

        Update history

        The write solution can maintain a change log. Logged changes can be used to repeat missing updates and to

        perform Event Sourcing to selectively update the query database.

        CQRS is an alternative to the strategy of each Microservice

        storing a separate Data Module in a Self-Managed Data Store . When a Microservice manages its own data in its own database, it can avoid the complexities that CQRS handles. CQRS is most useful with monolithic databases of data that has not been modularized. Until those databases and their applications can be modernized, Cloud Applications have to coexist with them, and CQRS is an approach for coexistence.

        If a Microservice has a complex data model and its clients concurrently update the data while reading it, the Microservice may benefit from implementing its Self-Manged Data Store using the CQRS design. A Microservice with a complex data model needs a domain model to keep the data valid. Meanwhile, multiple concurrent threads in multiple Microservice replicas can cause conflicts between the concurrent updates. Multiple Microservice threads attempting to read the data can conflict with other threads that are updating the data. Just like CQRS can help multiple applications coordinate, it can also help multiple threads in the same Microservice coordinate.

        CQRS is not limited to two databases. If multiple querying clients want very different views of the data, design a retrieve API for each along with a separate query database optimized for that API. All of the query databases can synchronize with the database of record by all subscribing to the event backbone for the update event notifications. Likewise, a query database can replicate data from multiple databases of record that each have their own modify APIs, as long as each write solution manages a separate set of data. All of those write solutions publish their updates as event notifications on the event backbone, which the query database merges into one combined set of read-only data.

        Querying clients must be designed to expect eventual consistency. CQRS introduces latency between the database of record and the query database that leads to eventual consistency between the updating clients and the querying clients.

        Designing the modify and retrieve APIs can be daunting for developers accustomed to direct database access, turning that

        access into contracts akin to Service APIs . The APIs make accessing the database into tasks that can be performed on behalf of the client. Implementing the modify API requires mastering the command pattern and message queuing.

        Command Query Responsibility Segregation separates clients that update data from those that query it, combining two synchronized databases that act as one. This separates handling of concurrent updates to complex data structures from concurrent querying of the data as it’s being updated, performing both tasks more efficiently. It is able to perform both inserts and queries efficiently since the read solution and write solution can use different database architectures.

        CQRS is a complex solution to a complex problem. The synchronization must work well or the read clients will query incorrect data. The read-and-write solutions are more complicated than direct database access. One challenge of CQRS is that it is arguably more complicated. Complexity has been moved from the database into the application. For those used to dealing with Relational Databases, the transfer of complexity can be difficult to adapt to. You also have to deal with eventual consistency. CQRS makes the asynchronous aspects explicit, but it can take some getting used to especially because it is unfamiliar to most developers. They may have to learn additional database technologies.

        Event Backbone is a key component of a CQRS solution, connecting the write and read solutions and implementing the basis for synchronizing the databases.

        CQRS is an amazingly powerful idea. CQRS was introduced to

        most people in CQRS by Martin Fowler. It has been elaborated

        further in many places, such as Command-Query

        Responsibility Segregation (CQRS), which also elaborates on the transformation from a simple application using a database to a full-blown CQRS solution.

        Examples

        The following examples illustrate some implementation considerations for CQRS and an example of refactoring to get the benefits of CQRS.

        Implementation variations

        Command Query Responsibility Segregation (CQRS) is a technique inspired by Bertrand Meyer’s “command query separation.” The basic idea behind CQRS is to separate commands from queries. Commands are operations that change data (and don’t return any data). Queries are operations that read data but don’t change anything. In distributed systems, changing data efficiently and consistently is challenging. Commands require a more complex design than queries. Also, it’s common for query operations to be called far more often than command operations. There are design alternatives for separating queries from commands when implementing CQRS. You need to decide whether to implement it either with One Service or Two Services. Query operations read from a dedicated data store, which is a replica of the primary data store that is updated by command operations. The query data store can be optimized for queries.

        One service

        In a single service, you separate query from command operations, but they’re still part of the same service. Query processor and command processor share some of the service logic. You include an optimized query data store for quick

        queries (read-only) of the data (see Figure 7-33).





        Figure 7-33. CQRS one service implementation

        Data from the “primary data store” is replicated to the “query data store,” which can be either internal or external to the service. For example, you might optimize your queries by creating an in-memory database. Because the data is replicated, it is important to note that sometimes you might be querying stale data.

        Two services

        You can also implement CQRS with two services (Figure 7-34), each with its own contract and design. This approach gives you more flexibility for independently scaling the query and command operations.



        Figure 7-34. CQRS two-service implementation

        For example, you can deploy the query service to 20 instances and the command service to 3 instances. You could then have the query service get data from Elastic Search while the command service uses MySql.

        Refactoring example

        Let’s give an example of when CQRS becomes important. Let’s say we have a team that is not operating in a complete greenfield—there are existing sources of functionality or data that must be reused to complete the application on time and within budget. In particular, you cannot transition all at once to a Cloud Database because critical data is stored in a large, existing monolithic database. In that case, how do you deal with the fact that you can’t usually transition all at once between existing monolithic data stores and the database-per-microservice approach?

        The problem is that reading from data is different from writing data. A service implementation usually has a specific “projection” of a set of relational data that represents a specific view of the data. That view can usually be cached using any of the data caching patterns described in this pattern language. The issue is that writing to the database often involves writing to multiple tables with complex business rules dictating how the information being written needs to be validated and updated. It’s that latter code, often encoded in legacy applications, that is difficult to change.

        One of the key aspects of CQRS is that when it is used for modernization purposes, it requires a data replication approach to keep the Read Model and the Write Model in synchronization. In some cases, this can be done with specific data synchronization tools for the databases being used for the

        Read Model and Write Model (for instance, Oracle GoldenGate

        or IBM DataGate), but these technologies often have significant limitations on which databases can be used for the data source and the data target.

        However, by combining existing patterns, we can accomplish this more generally. We create a new Read Model that is a projection of a data set in an existing application by creating a

        brand new Domain Microservice . We have also created a new

        Write Model that is an Adapter Microservice that translates from the new API to the existing API of the old application. This will require us to set up some type of data replication between the two so the projection of the existing data will keep up with

        changes to the Write Model. See Figure 7-35.





        Figure 7-35. CQRS data replication

        The most common way of setting up this data replication in this

        case would be by introducing an Event Backbone between the

        existing application and the Microservice that is serving as the

        Read Model (Figure 7-36). In this way, the new Read Model can subscribe to changes made to the existing system and update its data accordingly.





        Figure 7-36. CQRS with Event Backbone

        The update events can be created directly in the existing application if you have the ability to modify the existing application. That is by far the most general-purpose solution for this problem. But if you do not, you can still use a technology like Change Data Capture to record changes to the application’s underlying database. Many existing Change Data Capture tools,

        such as IBM Infosphere Change Data Capture and Oracle GoldenGate support connecting to a Kafka Event Backbone

        directly, as do open source platforms like Debezium.

        What’s more, you can even take this further. By introducing

        Event Sourcing , you don’t even necessarily need a database for your Read Model that represents the point-in-time. Instead, we can simply re-create the current state by reading the event

        sequence either stored directly on the Event Backbone or in a longer-term archival event database.
        """
}