<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:rng="http://relaxng.org/ns/structure/1.0"
    >
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>
  <!-- allow js_class attribute in calendar view/-->
  <xsl:template match="rng:element[@name='calendar']">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
      <rng:optional><rng:attribute name="js_class"/></rng:optional>
    </xsl:copy>
  </xsl:template>
</xsl:stylesheet>
