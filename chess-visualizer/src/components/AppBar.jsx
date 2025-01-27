import React from 'react';
import { Navbar, Container } from 'react-bootstrap';

const AppBarComponent = () => {
  return (
    <Navbar bg="dark" variant="dark" expand="lg" className="mb-4">
      <Container>
        <Navbar.Brand href="#">Chess Ontology</Navbar.Brand>
      </Container>
    </Navbar>
  );
};

export default AppBarComponent;