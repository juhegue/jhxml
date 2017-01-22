template = """
<jasperReport xmlns="http://jasperreports.sourceforge.net/jasperreports" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://jasperreports.sourceforge.net/jasperreports http://jasperreports.sourceforge.net/xsd/jasperreport.xsd" name="template" language="groovy" pageWidth="595" pageHeight="842" columnWidth="555" leftMargin="20" rightMargin="20" topMargin="20" bottomMargin="20">
  <property name="ireport.zoom" value="1.0"/>
  <property name="ireport.x" value="0"/>
  <property name="ireport.y" value="0"/>
  <queryString language="xPath"><![CDATA[]]></queryString>
  <background>
    <band splitType="Stretch"/>
  </background>
  <title>
    <band height="79" splitType="Stretch"/>
  </title>
  <pageHeader>
    <band height="35" splitType="Stretch"/>
  </pageHeader>
  <columnHeader>
    <band height="61" splitType="Stretch"/>
  </columnHeader>
  <detail>
    <band height="125" splitType="Stretch"/>
  </detail>
  <columnFooter>
    <band height="45" splitType="Stretch"/>
  </columnFooter>
  <pageFooter>
    <band height="54" splitType="Stretch"/>
  </pageFooter>
  <summary>
    <band height="42" splitType="Stretch"/>
  </summary>
</jasperReport>
"""

field = """
  <field name="%s" class="java.lang.String">
    <fieldDescription><![CDATA[%s]]></fieldDescription>
  </field>
"""

propiedad = """
<property name="OPENERP_RELATIONS" value="[&apos;%s&apos;]"/>
"""

double = """$F{%s} == null ||
$F{%s} == "" ||
$F{%s} == "0.0" ||
$F{%s} == "0,0" ||
$F{%s} == "0.00" ||
$F{%s} == "0,00" ||
$F{%s} == "0.000" ||
$F{%s} == "0,000" ? 0.0 : new Double(Double.parseDouble($F{%s}))
"""

date = """$F{%s} == null ||
$F{%s} == "" ? null : (new SimpleDateFormat("dd/MM/yyyy").format( new SimpleDateFormat("yyyy-MM-dd").parse($F{%s})))
"""

